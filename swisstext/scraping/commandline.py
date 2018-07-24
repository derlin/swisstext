import logging
import threading
from queue import Queue

import click

# TODO find a cleaner way
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from swisstext.scraping.common.page_queue import PageQueue
from swisstext.scraping.config import Config
from swisstext.scraping.interfaces import *
from swisstext.scraping.pipeline import PipelineWorker, Pipeline

logger = logging.getLogger('swisstext.scraper')
logger_default_level = "info"
config: Config = None
pipeline: Pipeline
queue: Queue
gen_seeds = True


@click.group(invoke_without_command=True)
@click.option('-l', '--log-level', type=click.Choice(["debug", "info", "warning", "fatal"]),
              default=logger_default_level)
@click.option('-c', '--config-path', type=click.Path(dir_okay=False), default=None)
@click.option('--seed/--no-seed', default=gen_seeds, help="Generate seeds in the end.")
def cli(log_level, config_path, seed):
    # configure logger
    import sys
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.getLevelName(log_level.upper()),
        format="[%(name)-15s %(levelname)-5s] %(message)s")

    logging.getLogger('swisstext.scraping.tools.pattern_sentence_filter').setLevel(level=logging.WARNING)

    # instantiate configuration and global variables
    global config, queue, pipeline, gen_seeds
    config = Config() if config_path is None else Config(config_path)
    pipeline = config.create_pipeline()
    queue = PageQueue()
    gen_seeds = seed


@cli.command('gen_seeds')
@click.option('-s', '--num-sentences', type=int, default=100, help="Number of sentences to use.")
@click.option('-n', '--num', type=int, default=5, help="Number of seeds to generate.")
@click.option('--new/--any', default=False, help="Use the newest sentences")
def gen_seeds(num_sentences, num, new):
    from swisstext.mongo.models import MongoSentence
    from mongoengine import connect
    with connect(**config.get('saver_options')):
        if new:
            sentences = [s.text for s in MongoSentence.objects \
                .fields(text=True) \
                .order_by('-date_added') \
                .limit(num_sentences)]
        else:
            aggregation_pipeline = [
                {
                    "$project": {'text': '$text'}
                },
                {
                    "$sample": {"size": num_sentences}
                }
            ]
            sentences = [s['text'] for s in MongoSentence.objects.aggregate(*aggregation_pipeline)]

    seeds = pipeline.seeder.generate_seeds(sentences, max=num)
    pipeline.saver.save_seeds(seeds)


@cli.command('from_mongo')
@click.option('-n', '--num-urls', type=int, default=20, help="Max URLs crawled in one pass.")
@click.option('--new/--any', default=False, help="Only crawl new URLs")
def crawl_mongo(num_urls, new):
    from swisstext.mongo.models import MongoURL
    from mongoengine import connect
    with connect(**config.get('saver_options')):
        if new:
            for u in MongoURL.get_never_crawled().fields(id=True).limit(num_urls):
                enqueue(u.id)
        else:
            aggregation_pipeline = [
                {
                    "$project": {
                        'last_crawl': {"$ifNull": ["$delta_date", None]},
                        'num_crawls': {"$size": {"$ifNull": ["$crawl_history", []]}}
                    }
                },
                {
                    "$sort": {"num_crawls": 1, "last_crawl": 1}
                },
                {
                    "$limit": num_urls
                }
            ]
            for u in MongoURL.objects.aggregate(*aggregation_pipeline):
                print(u)
                enqueue(u['_id'])

    logger.info("Enqueued %d URLs from Mongo" % queue.unfinished_tasks)
    crawl()


@cli.command('from_file')
@click.argument('urlfile', type=click.File('r'))
def crawl_from_file(urlfile):
    for u in urlfile:
        if u.startswith("http") and not pipeline.saver.is_url_blacklisted(u):
            enqueue(u.strip())
    crawl()


def enqueue(url):
    queue.put((pipeline.saver.get_page(url), 1))


def crawl():
    # one thread, 18 urls = ~ 30 seconds
    import time
    start = time.time()

    MAX_DEPTH = config.options.crawl_depth
    NUM_WORKERS = config.options.num_workers

    new_sentences: List[str] = []
    args = (queue, pipeline, new_sentences, MAX_DEPTH)

    # launch multiple workers
    if NUM_WORKERS > 1:
        threads = []
        for i in range(NUM_WORKERS):
            t = threading.Thread(target=PipelineWorker().run, args=args)
            t.start()
            threads.append(t)

        # block until all tasks are done
        for t in threads:
            t.join()

    else:
        # only one worker -> don't bother with threads
        worker = PipelineWorker()
        worker.run(*args)

    logger.info("Found %d new sentences." % len(new_sentences))

    with open('/tmp/new_sentences.txt', 'w') as f:
        f.write("\n".join(new_sentences))

    # TODO: call a
    if gen_seeds:
        if len(new_sentences):
            for seed in pipeline.seeder.generate_seeds(new_sentences):
                pipeline.saver.save_seed(seed)
        else:
            print("No new sentence found.")

    stop = time.time()
    print("Done. It took {} seconds.".format(stop - start))


if __name__ == "__main__":
    cli()
