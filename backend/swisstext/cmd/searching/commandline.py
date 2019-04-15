#!/user/bin/env python3
# -*- coding: utf-8 -*-

"""
This module contains the commandline interface for the searcher.

Usage
-----

Use the `--help` option to discover the capabilities and options of the tool.
"""

from typing import Iterable

import click
import logging

from .pipeline import SearchEngine
from .config import Config
from .data import Seed

# ============== global variables

logger = logging.getLogger('swisstext.searching')
logger_default_level = "info"


class GlobalOptions:

    def __init__(self, config_path: str = None, db: str = None):
        self._config_path = config_path
        self._config: Config = None
        self._db = db
        self._search_engine: SearchEngine = None

    @property
    def config(self) -> Config:
        if self._config is None:
            self._config = Config() if self._config_path is None else Config(self._config_path)
            if self._db: self._config.set('saver_options.db', self._db)
        return self._config

    @property
    def search_engine(self) -> SearchEngine:
        if self._search_engine is None:
            self._search_engine = self.config.create_search_engine()
        return self._search_engine


# ============== main entrypoint

@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-l', '--log-level', type=click.Choice(["debug", "info", "warning", "fatal"]),
              default=logger_default_level)
@click.option('-d', '--db', default=None, help='If set, this will override the database set in the config')
@click.option('-c', '--config-path', type=click.Path(dir_okay=False), default=None)
@click.pass_context
def cli(ctx, log_level, db, config_path):
    # configure logger
    import sys
    logging.basicConfig(
        stream=sys.stderr,
        format="'%(asctime)s [%(name)-15s %(levelname)-5s] %(message)s",
        datefmt='%Y-%m-%dT%H:%M:%S')

    # only set the logging level on our classes
    logging.getLogger('swisstext').setLevel(logging.getLevelName(log_level.upper()))

    # instantiate configuration and global variables
    ctx.obj = GlobalOptions(config_path, db)


# ============== available commands

@cli.command('dump_config')
@click.pass_obj
def dump_config(ctx):
    """Prints the active configuration."""
    import pyaml
    print(pyaml.dump(ctx.config.conf))


@cli.command('from_mongo')
@click.option('-n', '--num-seeds', type=int, default=20, help="Max seeds used.")
@click.option('--new/--any', default=False, help="Only search new seeds")
@click.pass_obj
def from_mongo(ctx, num_seeds, new):
    """
    This script runs the search engine system using -n seeds pulled from Mongo. Those seeds are
    selected depending on the number of usages and the date of the last use (less used first, oldest usage first).
    If --new is specified, only seeds that have never been used will be queried.
    If --any is specified, exactly -n seeds are selected.

    Note that to connect to MongoDB, it relies on the host, port and db options present in the `saver_options` property
    of the configuration. So whatever saver you use, ensure that those properties are correct
    (default: localhost:27017, db=swisstext).
    """
    from swisstext.mongo.models import MongoSeed, get_connection
    with get_connection(**ctx.config.get('saver_options')):
        if new:
            # just get the seeds that have never been used (give priority to user seeds)
            queryset = MongoSeed.objects(search_history__0__exists=False) \
                .order_by("-source.type") \
                .fields(id=True) \
                .limit(num_seeds)
            seeds = (s.id for s in queryset)
        else:
            # origin: user vs auto... we want the user to have the priority => sort descending (origin: -1)
            aggregation_pipeline = [
                {"$project": {
                    'num_searches': {"$size": {"$ifNull": ["$search_history", []]}},
                    'origin': "$source.type",
                    'date_added': "$date_added",
                    'last_searched': {"$ifNull": ["$delta_date", None]}
                }},
                {"$sort": {"num_searches": 1, "origin": -1, "date_added": 1, "last_searched": 1}},
                {"$limit": num_seeds}
            ]
            seeds = (s['_id'] for s in MongoSeed.objects.aggregate(*aggregation_pipeline))

    _search(ctx, seeds)


@cli.command('from_file')
@click.argument('seedsfile', type=click.File('r'))
@click.pass_obj
def from_file(ctx, seedsfile):
    """
    Search using seeds from a file.

    This script runs the search engine using the query terms present in a file.
    The file should have one seed per line; any line starting with a space will ignored.
    Seeds and results will be persisted using the configured saver.
    """
    seeds = (l.strip() for l in seedsfile if l and not l.startswith(" "))
    _search(ctx, seeds)


def _search(ctx: GlobalOptions, seeds: Iterable[str]):
    # do the magic
    import time
    start = time.time()
    tasks = [Seed(s) for s in seeds]
    logger.info("About to search %d seeds" % len(tasks))
    new_urls_found = ctx.search_engine.process(tasks, max_results=ctx.config.options.max_results)
    logger.info('Found %d new URLs.' % new_urls_found)
    stop = time.time()
    print("Done. It took {} seconds.".format(stop - start))
