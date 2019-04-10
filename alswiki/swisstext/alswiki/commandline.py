#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import click

from .data import *

from swisstext.cmd.scraping.config import Config
from swisstext.cmd.scraping.page_queue import PageQueue
from swisstext.cmd.scraping.pipeline import Pipeline

from smart_open import open as smart_open
from gensim.scripts.segment_wiki import segment_and_write_all_articles

logger = logging.getLogger('swisstext.cmd.scraper')
logger_default_level = "info"


# ============== main entrypoint

@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-l', '--log-level', type=click.Choice(["debug", "info", "warning", "fatal"]),
              default=logger_default_level)
def cli(log_level):
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

    print(f'Parsing dump using gensim (might take a while).')
    jsonfile = dumpfile.replace('.xml', '.json')

    segment_and_write_all_articles(
        dumpfile, jsonfile,
        min_article_character=min_chars,
        workers=1,
        include_interlinks=False
    )
    print(f'Dump written in {jsonfile}')