import logging
from queue import Queue

from swisstext.interfaces import *
from swisstext.common.data import Sentence, Page

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(self,
                 crawler: ICrawler, splitter: ISplitter, filter: ISentenceFilter,
                 detector: ISgDetector, seeder: ISeedCreator, decider: IDecider,
                 saver: IPageSaver, min_proba=0.85):
        self.crawler = crawler
        self.filter = filter
        self.splitter = splitter
        self.detector = detector
        self.seeder = seeder
        self.saver = saver
        self.decider = decider
        self.min_proba = min_proba


class PipelineWorker:
    def __init__(self):
        pass

    def run(self, queue: Queue, p: Pipeline, new_sentences: List[str], max_depth=1):
        while not queue.empty():
            (page, page_depth) = queue.get()
            logger.debug("Processing: %s (depth=%d)" % (page.url, page_depth))
            if page_depth > max_depth:
                logging.info(
                    "reached max depth for recursive scraping (still %d links in queue). Exiting." % queue.qsize())
                break

            if p.decider.should_page_be_crawled(page):
                try:
                    page.crawl_results = p.crawler.crawl(page.url)
                    splitted: List[str] = p.splitter.split(page.crawl_results.text)
                    sentences: List[str] = p.filter.filter(splitted)
                    page.sentence_count = 0
                    ns = []
                    for (s, proba) in zip(sentences, p.detector.predict(sentences)):
                        page.sentence_count += 1
                        if proba >= p.min_proba:
                            page.sg_count += 1
                            if not p.saver.sentence_exists(s):
                                ns.append(s)
                                page.new_sg.append(Sentence(s, proba))

                    if ns: new_sentences.extend(ns)

                    if p.decider.should_url_be_blacklisted(page):
                        logger.info("blacklisting %s" % page.url)
                        p.saver.blacklist_url(page.url)

                    else:
                        p.saver.save_page(page)
                        if page_depth < max_depth and p.decider.should_children_be_crawled(page):
                            added_children = 0
                            for l in page.crawl_results.links:
                                if not p.saver.is_url_blacklisted(l):
                                    child_page = p.saver.get_page(l, source=page.url)
                                    # TODO redondant ?
                                    if p.decider.should_page_be_crawled(child_page):
                                        queue.put((child_page, page_depth + 1))
                                        added_children += 1
                            logger.debug("%s: added %d child URLs" % (page.url, added_children))

                except Exception as e:

                    if not isinstance(e, ICrawler.CrawlError):
                        logger.exception(e)
            else:
                logger.debug("Skipped '%s'" % page.url)
        queue.task_done()
