"""
This module contains the core of the scraping system.

In order to be fully customizable, it uses the concept of interfaces heavily: most of the decisions and steps
are delegated to instances of classes defined in :py:mod:`~swisstext.cmd.scraping.interfaces`.

Here is an example usage.

.. code-block:: python

    from swisstext.cmd.scraping.pipeline import Pipeline, PipelineWorker
    from swisstext.cmd.scraping.data import Page
    from swisstext.cmd.scraping.page_queue import PageQueue
    from swisstext.cmd.scraping.config import Config
    from typing import List

    # print some information to the console
    import logging
    logging.basicConfig(stream=sys.stdout)
    logging.getLogger('swisstext').setLevel(level=logging.INFO)

    queue: PageQueue = PageQueue()
    new_sentences: List[str] = []

    # load the config and create the default pipeline
    # WARNING: the default config will try to connect to MongoDB on localhost:27017
    # if you don't want to use Mongo, create a config file and use the ConsoleSaver instead
    # or use the hack: pipeline.saver = ConsoleSaver()
    config = Config(config_path=None) # set the config path if you have one
    pipeline = config.create_pipeline()

    # add one page to the queue
    start_url = 'http://www.hunold.ch/zw/goeteborg.html'
    queue.put((Page(start_url), 1)) # add the tuple (url, depth) with a depth of 1

    # launch one worker
    worker = PipelineWorker()
    worker.run(queue, pipeline, new_sentences, max_depth=config.options.crawl_depth)



.. todo:

    What should we do when an error occurs during download ? Should an inaccessible page be blacklisted ?
"""

import logging
from queue import Queue, Empty

from .interfaces import *
from .data import Sentence

logger = logging.getLogger(__name__)

GET_TIMEOUT = 60 * 3  # in seconds


class Pipeline:
    """
    Holds instances of all needed interfaces and variables.

    Note that pipelines are meant to be instantiated by a :py:class:`~swisstext.cmd.scraping.config.Config` object,
    not manually.
    """

    def __init__(self,
                 crawler: ICrawler,
                 normalizer: INormalizer,
                 splitter: ISplitter,
                 filter: ISentenceFilter,
                 detector: ISgDetector,
                 seeder: ISeedCreator,
                 decider: IDecider,
                 saver: ISaver,
                 min_proba=0.85):
        self.crawler: ICrawler = crawler
        self.normalizer: INormalizer = normalizer
        self.splitter: ISplitter = splitter
        self.filter: ISentenceFilter = filter
        self.detector: ISgDetector = detector
        self.seeder: ISeedCreator = seeder
        self.saver: ISaver = saver
        self.decider: IDecider = decider
        self.min_proba = min_proba


class PipelineWorker():
    """
    Pipeline workers actually do the magic and can be run in parallel.
    """

    def __init__(self, id=-1):
        self.id = id
        """an identifier used in log messages, especially useful if multiple threads are used."""
        self.kill_received = False
        """
        If the worker is launched in a thread, you can use this flag to make it exit prematurely.
        Workers will always finish processing the current page before exiting, so that we can ensure
        coherence in the persistence layer.
        """

    def _crawl_page(self, crawler: ICrawler, page: Page):
        """ Override in case we need page information to crawl """
        return crawler.crawl(page.url)

    def run(self, queue: Queue, p: Pipeline, new_sentences: List[str], max_depth=1):
        """
        Do the work ! All the magic is in here :)

        For each page pulled from the queue, the worker will execute all the steps of the scraping pipeline:

        * get text and links,
        * split and filter sentences,
        * keep sentences with Swiss German,
        * persist the results (url + sentences), if any
        * add new tasks to the queue (if the page contains links to interesting URLs)

        New sentences are added to the new_sentences list, so that the caller can easily know how fruitful the
        scraping was and optionaly use the new sentences to generate seeds.

        This method will stop:

        * when the queue is empty or
        * if the :py:attr:`kill_received` is set to true. In this case, it finishes processing the current task and exit

        .. warning::

            It is your responsibility to ensure that the URLs in the queue are not blacklisted.

        .. todo::

            This piece of code (and the commandline) has many flaws and should clearly be enhanced... For example:

            **Multithreading**: currently, the worker stops when the queue is empty. This also means that if
            you launch the system with only 3 base urls but 5 workers, 2 workers will exit immediately instead
            of waiting for new tasks to be added to the queue.

            A better way would be to keep track of active workers and stop only when all workers are idle, or
            when all workers reached a task with a depth > max depth...

            **Comportement on errors**: in case fetching the URL triggers an error, we currently just log the thing.
            Should we also remove/blacklist the URL ? Should we allow the URL to fail X times before removal ?

        :param queue: the task queue
        :param p: the pipeline to use
        :param new_sentences: all new sentences discovered will be added to this list
        :param max_depth: when do we stop (inclusive)
        """
        while not queue.empty():

            if self.kill_received:
                logger.info(f'W[{self.id}]: Kill received, stopping.')
                return

            try:
                (page, page_depth) = queue.get(timeout=GET_TIMEOUT)  # blocking !!
            except Empty:
                logger.error(f'W[{self.id}]: Empty exception was raised.')
                break

            logger.debug(f'W[{self.id}]: processing {page.url} (depth={page_depth})')
            if page_depth > max_depth:
                logger.info(
                    f'W[{self.id}]: reached max depth for recursive scraping (still ${queue.qsize()} links in queue).')
                break

            if p.decider.should_page_be_crawled(page):
                try:
                    page.crawl_results = self._crawl_page(p.crawler, page)
                    page.text = p.normalizer.normalize(page.crawl_results.text)
                    splitted: List[str] = p.splitter.split(page.text)
                    sentences: List[str] = p.filter.filter(splitted)

                    page.sentence_count = 0  # count all the sentences found
                    ns = []  # register new sentences here

                    # TODO: change the detector interface to avoid zipping ?
                    for (s, proba) in zip(sentences, p.detector.predict(sentences)):
                        page.sentence_count += 1
                        if proba >= p.min_proba:
                            page.sg_count += 1
                            if not p.saver.sentence_exists(s):
                                ns.append(s)
                                page.new_sg.append(Sentence(s, proba))

                    # update the new_sentences just once (extend is atomic)
                    if ns: new_sentences.extend(ns)

                    if p.decider.should_url_be_blacklisted(page):
                        logger.info(f'W[{self.id}]: blacklisting {page.url}')
                        p.saver.blacklist_url(page.url)

                    else:
                        p.saver.save_page(page)
                        if p.decider.should_children_be_crawled(page):
                            added_children = 0
                            for l in page.crawl_results.links:
                                if not p.saver.is_url_blacklisted(l):
                                    child_page = p.saver.get_page(l, parent_url=page.url)
                                    # TODO redondant ?
                                    if p.decider.should_page_be_crawled(child_page):
                                        queue.put((child_page, page_depth + 1))
                                        added_children += 1
                            logger.info(f'W[{self.id}] {page.url}: added {added_children} child URLs')

                except Exception as e:
                    # TODO blacklist url ?
                    if isinstance(e, ICrawler.CrawlError):
                        p.saver.blacklist_url(page.url, error_message=e.name)
                        logger.info(f'W[{self.id}]: exception -- {e}. Blacklisted.')
                    else:
                        logger.exception(f'An error occurred while processing {page.url}')

            else:
                logger.debug(f'W[{self.id}]: skipped {page.url}')

            queue.task_done()

        if self.id >= 0:
            logger.info(f'W[{self.id}]: my job is done.')
