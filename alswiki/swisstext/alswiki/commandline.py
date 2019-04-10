#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module contains commandline tools to process `alemannische wikipedia <als.wikipedia.org>_` dumps.

Usage
-----

Use the `--help` option to discover the capabilities and options of the tool.


.. todo::

    Also exit cleanly when only one worker runs in the main thread

"""

import logging
import click

from .data import *

from swisstext.cmd.scraping.config import Config
from swisstext.cmd.scraping.page_queue import PageQueue
from swisstext.cmd.scraping.pipeline import Pipeline

from smart_open import open as smart_open
from gensim.scripts.segment_wiki import segment_and_write_all_articles

logger = logging.getLogger('swisstext.alswiki')
logger_default_level = "info"


# ============== main entrypoint

@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-l', '--log-level', type=click.Choice(["debug", "info", "warning", "fatal"]),
              default=logger_default_level)
def cli(log_level):
    """
    A suite of tools for downloading, parsing and processing wikipedia dumps.
    """
    import sys
    # configure all loggers (log to stderr)
    logging.basicConfig(
        stream=sys.stderr,
        format="'%(asctime)s [%(name)-15s %(levelname)-5s] %(message)s",
        datefmt='%Y-%m-%dT%H:%M:%S')

    # only set the logging level on our classes
    logging.getLogger('swisstext').setLevel(logging.getLevelName(log_level.upper()))
    # silence this very verbose tool...
    logging.getLogger('swisstext.cmd.scraping.tools.pattern_sentence_filter').setLevel(level=logging.WARNING)


# ============== commands

@cli.command('process')
@click.option('-c', '--config-path', type=click.Path(dir_okay=False), default=None)
@click.option('-d', '--db', default=None, help='If set, this will override the database set in the config')
@click.argument('gensimfile')
def process(config_path, db, gensimfile):
    """
    Process articles using the scraping pipeline.

    <config-path> and <db> are the same as in ``st_scrape``.
    The <gensimfile> can be either in json or json.bz2. To generate it:

    1. download an "alswiki-*-pages-articles.xml.bz2" from
       https://dumps.wikimedia.org/alswiki (or use the download command),

    2. use gensim's segment_wiki tool (python -m gensim.scripts.segment_wiki -h)
       to extract articles (in json format) from the raw dump (or use the parse command)
    """
    # instantiate configuration and global variables
    config = Config() if config_path is None else Config(config_path)
    if db: config.set('saver_options.db', db)
    pipeline: Pipeline = config.create_pipeline()
    queue = PageQueue()

    new_sentences = []
    worker = PipelineWorkerWrapper()

    for line in smart_open(gensimfile):
        article = Article(line)
        if not pipeline.saver.is_url_blacklisted(article.url):
            page = pipeline.saver.get_page(article.url)
            page.article = article
            queue.put((page, 1))  # set depth to 1
            # pagewrap = PageWrapper(page, article)
            # queue.put((pagewrap, 1))  # set depth to 1
            worker.run(queue, pipeline, new_sentences, 1)


@cli.command('download')
@click.option('-d', '--dir', help='directory where to download files', default='.')
def download_latest(dir):
    """
    Download the latest dump of als.wikipedia.org.

    It will save alswiki-latest-pages-articles.xml.bz2 in the directory given by <dir>.
    """
    import requests
    from os.path import join as path_join

    url = 'https://dumps.wikimedia.org/{lang}wiki/latest/{lang}wiki-latest-pages-articles.xml.bz2'.format(lang='als')
    raw_dump_path = path_join(dir, url.split('/')[-1])

    r = requests.get(url, stream=True)
    if r.status_code == 200:
        print_dots = logger.getEffectiveLevel() <= logging.INFO
        with open(raw_dump_path, 'wb') as f:
            for i, chunk in enumerate(r):
                f.write(chunk)
                if print_dots and i % (2048) == 0:
                    print('.', end='', flush=True)
        if print_dots:
            print('\n')
    logger.info(f'Downloaded wiki dump into {raw_dump_path}')


@cli.command('parse')
@click.option('-m', '--min-chars',
              help="Ignore articles with fewer characters than this (article stubs)",
              default=200)
@click.argument('dumpfile')
def parse(dumpfile, min_chars):
    """
    Extract articles from a wiki dump.

    <dumpfile> must be a wiki-*-pages-articles.xml.bz2 file. The output file
    will be saved alongside the dump with the json.bz2 extension.
    See gensim's segment_wiki tool for more details (python -m gensim.scripts.segment_wiki -h).
    """
    print(f'Parsing dump using gensim (might take a while).')
    jsonfile = dumpfile.replace('.xml', '.json')

    segment_and_write_all_articles(
        dumpfile, jsonfile,
        min_article_character=min_chars,
        workers=1,
        include_interlinks=False
    )
    print(f'Dump written in {jsonfile}')