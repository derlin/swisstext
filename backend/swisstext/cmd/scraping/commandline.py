#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module contains the commandline interface for the scraper.

Usage
-----

Use the `--help` option to discover the capabilities and options of the tool.

"""
import logging
import threading
from functools import partial

import click

from swisstext.cmd import link_utils
from .page_queue import PageQueue
from .config import Config
from .interfaces import *
from .pipeline import PipelineWorker, Pipeline

# ============== global variables

logger = logging.getLogger('swisstext.cmd.scraper')
logger_default_level = "info"

click.option = partial(click.option, show_default=True)  # show default in help (see click issues #646)


class GlobalOptions:
    """Hold the options used by all tools, using lazy instantiation if possible."""

    def __init__(self, config_path: str = None, gen_seeds=False, db: str = None):
        """
        :param config_path: path to an optional user configuration path
        :param gen_seeds: whether or not to generate seeds
        :param db: name of the mongo db to use
        """
        self.gen_seeds = gen_seeds

        self._config_path = config_path
        self._config: Config = None
        self._db = db
        self._pipeline: Pipeline = None

        self.queue = PageQueue()

    @property
    def config(self) -> Config:
        """Configuration object (lazy loaded)."""
        if self._config is None:
            self._config = Config() if self._config_path is None else Config(self._config_path)
            if self._db: self._config.set('saver_options.db', self._db)
        return self._config

    @property
    def pipeline(self) -> Pipeline:
        """Pipeline holding the tool instances (lazy loaded)."""
        if self._pipeline is None:
            self._pipeline = self.config.create_pipeline()
        return self._pipeline


# ============== main entrypoint

@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-l', '--log-level', type=click.Choice(["debug", "info", "warning", "fatal"]),
              default=logger_default_level)
@click.option('-c', '--config-path', type=click.Path(dir_okay=False), default=None)
@click.option('-d', '--db', default=None, help='If set, this will override the database set in the config')
@click.pass_context
def cli(ctx, log_level, config_path, db):
    import sys
    # configure all loggers (log to stderr)
    logging.basicConfig(
        stream=sys.stderr,
        format="%(asctime)s [%(name)-15s %(levelname)-5s] %(message)s",
        datefmt='%Y-%m-%dT%H:%M:%S')

    # only set the logging level on our classes
    logging.getLogger('swisstext').setLevel(logging.getLevelName(log_level.upper()))
    # silence this very verbose tool...
    logging.getLogger('swisstext.cmd.scraping.tools.pattern_sentence_filter').setLevel(level=logging.WARNING)

    # instantiate configuration and global variables
    ctx.obj = GlobalOptions(config_path, gen_seeds, db)


# ============== available commands

@cli.command('dump_config')
@click.option('-t', '--test', is_flag=True, help='Also instantiate the tools')
@click.pass_obj
def dump_config(ctx, test):
    """
    Prints the active configuration. If <test> is set, the pipeline is also instantiated,
    ensuring all tool names exist and use correct options.
    """
    print(ctx.config.dumps())
    if test:
        try:
            print('Instantiating tools...')
            ctx.config.instantiate_tools()
            print('Success.')
        except Exception as e:
            raise Exception('Error instantiating tools.') from e


@cli.command('gen_seeds')
@click.option('-s', '--num-sentences', type=int, default=100, help="Number of sentences to use.")
@click.option('-n', '--num', type=int, default=5, help="Number of seeds to generate.")
@click.option('--new/--any', default=False, help="Use the newest sentences")
@click.option('-c', '--confirm', is_flag=True, default=False, help="Ask for confirmation before saving.")
@click.pass_obj
def gen_seeds(ctx, num_sentences, num, new, confirm):
    """
    Generate seeds from a sample of mongo sentences.

    This script generates -n seeds using a given number of sentences (-s) pulled from MongoDB.
    If --new is specified, the latest sentences are used (date_added).
    If --any is specified, sentences are selected randomly.

    Note that: (1) seeds will be saved to the persistence layer using the saver class specified in the configuration.
    (2) to connect to MongoDB, it relies on the host, port and db options present in the `saver_options` property
    of the configuration. So whatever saver you use, ensure that those properties are correct
    (default: localhost:27017, db=swisstext).
    """
    from swisstext.mongo.models import MongoSentence, get_connection
    with get_connection(**ctx.config.get('saver_options')):
        if new:
            # simply order sentences by date_added, descending
            sentences = [s.text for s in MongoSentence.objects \
                .fields(text=True) \
                .order_by('-date_added') \
                .limit(num_sentences)]
        else:
            # use the $sample utility of Mongo to get a random sample of sentences
            aggregation_pipeline = [
                {"$project": {'text': '$text'}},
                {"$sample": {"size": num_sentences}}
            ]
            sentences = [s['text'] for s in MongoSentence.objects.aggregate(*aggregation_pipeline)]

    seeds = ctx.pipeline.seeder.generate_seeds(sentences, max=num)
    if confirm:
        for seed in seeds:
            if click.confirm(seed):
                ctx.pipeline.saver.save_seed(seed)
    else:
        ctx.pipeline.saver.save_seeds(seeds)


@cli.command('from_mongo')
@click.option('-n', '--num-urls', type=int, default=20, help="Max URLs crawled in one pass.")
@click.option('--what', type=click.Choice(['any', 'new', 'ext']), default='any',
              help='Pull any URLs / new URLs / new URLs from external source (seed, file)')
@click.option('--how', type=click.Choice(['oldest', 'random']), default='oldest',
              help='Pull URLs oldest first / at random')
@click.pass_obj
def crawl_mongo(ctx, num_urls, what, how):
    """
    Scrape using mongo URLs as base.

    This script runs the scraping pipeline using -n bootstrap URLs pulled from Mongo. Those URLs are
    selected depending on the number of visits and the date of the last visit (less visited first, oldest visit first).
    The --what argument can be used to control which URLs will be pulled from mongo to start the process.
    Use 'new' for URLs never visited before, 'seed' for non-visited URLs found using the search engine or 'any' (default).
    Except with what=any, the actual number of URLs pulled is not guaranteed to be -n.

    Note that to connect to MongoDB, it relies on the host, port and db options present in the `saver_options` property
    of the configuration. So whatever saver you use, ensure that those properties are correct
    (default: localhost:27017, db=swisstext).
    """

    # == create aggregation pipeline
    what_stage = {
        'any': {},  # no filtering
        'new': {"crawl_history.0": {"$exists": False}},  # just new
        'ext': {  # new AND from seed or file
            "crawl_history.0": {"$exists": False},
            "source.type": {"$ne": "auto"}
        }}
    how_stage = {
        'random': [{"$sample": {"size": num_urls}}],
        'oldest': [  # still prioritize non visited first
            {"$sort": {"num_crawls": 1, "last_crawl": 1, "added": 1}},
            {"$limit": num_urls}
        ]}
    aggregation_pipeline = \
        [
            {"$match": what_stage[what]},
            {"$project": {
                "url": "$url",
                "added": "$date_added",
                "typ": "$source.type",
                "extra": "$source.extra",
                "last_crawl": {"$ifNull": ["$delta_date", None]},
                "num_crawls": {"$size": {"$ifNull": ["$crawl_history", []]}}
            }}
        ] + how_stage[how]

    # == run query and enqueue results
    from swisstext.mongo.models import MongoURL, get_connection
    with get_connection(**ctx.config.get('saver_options')):

        for u in MongoURL.objects.aggregate(*aggregation_pipeline):
            # add
            if u['typ'] == 'auto' and u['extra'].startswith('http'):
                ok = _enqueue(ctx, u['url'], parent_url=u['extra'])
            else:
                ok = (_enqueue(ctx, u['url']))
            # log
            if ok:
                logger.debug(f"  {u['url']} {u['typ']} ({u['num_crawls']})")
            else:
                logger.error(f'URL {u.url} not enqueued.')

    logger.info("Enqueued %d URLs from Mongo" % ctx.queue.unfinished_tasks)
    _scrape(ctx.config, ctx.queue, ctx.pipeline)


@cli.command('from_file')
@click.argument('urlfile', type=click.File('r'))
@click.pass_obj
def crawl_from_file(ctx, urlfile):
    """
    Scrape using URLs in a file as base.

    This script runs the scraping pipeline using the URLs present in a file as bootstrap URLs.
    The file should have one URL per line. Any line starting with something other that "http" will be ignored.
    """
    for i, u in enumerate(urlfile):
        u = u.strip()
        if not u.startswith('#'):
            _enqueue(ctx, u)

    logger.info(f'enqueued {ctx.queue.unfinished_tasks}/{i + 1} URLs from {urlfile.name}.')
    _scrape(ctx.config, ctx.queue, ctx.pipeline)


# ============== main methods

def _enqueue(ctx, url, **kwargs) -> bool:
    fixed_url, interesting = link_utils.fix_url(url)
    if interesting and not ctx.pipeline.saver.is_url_blacklisted(fixed_url):
        ctx.queue.put((ctx.pipeline.saver.get_page(fixed_url, **kwargs), 1))  # set depth to 1
        return True
    return False


def _scrape(config, queue, pipeline, worker_cls=PipelineWorker):
    # stop right away if nothing to scrape
    if queue.empty():
        print('Nothing to scrape.')
        return

    # do the magic
    logger.info('Using config:\n' + config.dumps())

    import time
    start = time.time()

    MAX_DEPTH = config.options.crawl_depth
    NUM_WORKERS = config.options.num_workers

    new_sentences: List[str] = []
    args = (queue, pipeline, new_sentences, MAX_DEPTH)  # what to pass to the PipelineWorker's run method

    # launch multiple workers
    # TODO: use https://docs.python.org/3/library/concurrent.futures.html#processpoolexecutor instead ?
    if NUM_WORKERS > 1:
        # use multiple threads
        threads = []
        for i in range(min(NUM_WORKERS, queue.unfinished_tasks)):
            worker = worker_cls(i)
            t = threading.Thread(target=worker.run, args=args)
            t.start()
            threads.append((worker, t))

        # block until all tasks are done
        # in case ctrl+c is received, notify the threads using a flag
        # TODO make it cleaner !
        import signal
        def handler(signum, frame):
            print("Ctrl-c received! Sending kill to threads... Press again to force stop.")
            for w, t in threads:
                w.kill_received = True
            signal.signal(signal.SIGINT, signal.default_int_handler)

        signal.signal(signal.SIGINT, handler)

        for w, t in threads:
            t.join()

    else:
        # only one worker -> don't bother with threads
        worker = worker_cls()
        try:
            worker.run(*args)
        except KeyboardInterrupt:
            print('Interrupt received. Cleaning up...')
            pass

    logger.info("Found %d new sentences." % len(new_sentences))

    logger.debug('Saving non-scraped pages for later.')
    saved_urls = 0
    while not queue.empty():
        page, _ = queue.get()
        if page.parent_url is not None:
            try:
                # parent is None for initial URLs
                pipeline.saver.save_url(page.url, page.parent_url)
                saved_urls += 1
            except:
                logger.exception(f'Failed to save {page.url} for later.')
        queue.task_done()
    logger.info('Saved {} for later.'.format(saved_urls))

    stop = time.time()
    print("Done. It took {} seconds.".format(stop - start))

    # TODO remove
    with open('/tmp/new_sentences.txt', 'w') as f:
        f.write("\n".join(new_sentences))
