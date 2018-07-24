from typing import Iterable

import click
import logging

# TODO find a cleaner way
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from swisstext.searching.pipeline import SearchEngine
from swisstext.searching.config import Config
from swisstext.searching.data import Seed

logger = logging.getLogger('swisstext.searching')

logger_default_level = "info"
config: Config
search_engine: SearchEngine


@click.group(invoke_without_command=True)
@click.option('-l', '--log-level', type=click.Choice(["debug", "info", "warning", "fatal"]),
              default=logger_default_level)
@click.option('-c', '--config-path', type=click.Path(dir_okay=False), default=None)
def cli(log_level, config_path):
    # configure logger
    import sys
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.getLevelName(log_level.upper()),
        format="[%(name)-15s %(levelname)-5s] %(message)s")

    # instantiate configuration and global variables
    global config, search_engine
    config = Config() if config_path is None else Config(config_path)
    search_engine = config.create_search_engine()


@cli.command('from_mongo')
@click.option('-n', '--num-seeds', type=int, default=20, help="Max seeds used.")
@click.option('--new/--any', default=False, help="Only search new seeds")
def from_mongo(num_seeds, new):
    from swisstext.mongo.models import MongoSeed
    from mongoengine import connect
    with connect(**config.get('saver_options')):
        if new:
            seeds = (s.id for s in MongoSeed.objects(search_history__0__exists=False).fields(id=True).limit(num_seeds))
        else:
            # origin: user vs auto... we want the user to have the priority => sort descending (origin: -1)
            aggregation_pipeline = [
                {
                    "$project": {
                        'num_searches': {"$size": {"$ifNull": ["$search_history", []]}},
                        'origin': "$source.type",
                        'date_added': "$date_added",
                        'last_searched': {"$ifNull": ["$delta_date", None]}
                    }
                },
                {
                    "$sort": {"num_searches": 1, "origin": -1, "date_added": 1, "last_searched": 1}
                },
                {
                    "$limit": num_seeds
                }
            ]
            seeds = (s['_id'] for s in MongoSeed.objects.aggregate(*aggregation_pipeline))

    search(seeds)


@cli.command('from_file')
@click.argument('seedsfile', type=click.File('r'))
def from_file(seedsfile):
    seeds = (l.strip() for l in seedsfile if l)
    search(seeds)


def search(seeds: Iterable[str]):
    # one thread, 18 urls = ~ 30 seconds
    import time
    start = time.time()
    tasks = [Seed(s) for s in seeds]
    logger.info("About to search %d seeds" % len(tasks))
    search_engine.process(tasks, max_results=config.options.max_results)
    stop = time.time()
    print("Done. It took {} seconds.".format(stop - start))


if __name__ == "__main__":
    cli()
