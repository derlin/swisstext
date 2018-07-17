import logging
import sys
import threading
from queue import Queue

import click

from swisstext.common.page_queue import PageQueue
from swisstext.interfaces import *
from swisstext.tools.console_saver import ConsoleSaver
from swisstext.tools.mongo_saver import MongoSaver
from swisstext.pipeline import Pipeline, PipelineWorker
from swisstext.tools.basic_decider import BasicDecider
from swisstext.tools.basic_seed_creator import BasicSeedCreator
from swisstext.tools.bs_crawler import BsCrawler
from swisstext.tools.pattern_sentence_filter import PatternSentenceFilter
from swisstext.tools.punkt_splitter import PunktSplitter
from swisstext.tools.swigspot_langid import SwigspotLangid

logger = logging.getLogger('swisstext.pipeline')


@click.command()
@click.option('-p', '--proba', type=float, default=0.85, help="Min proba for SG")
@click.option('-d', '--depth', type=int, default=2, help="crawl depth")
@click.option('-s', '--source', type=str, default="recrawl")
@click.argument('urlfile', type=click.File('r'))
def crawl(proba, depth, source, urlfile):
    # one thread, 18 urls = ~ 30 seconds
    import time
    start = time.time()

    MAX_DEPTH = 1
    NUM_WORKERS = 1
    DB_NAME = "tmp"

    logging.basicConfig(stream=sys.stderr, format="[%(name)-15s %(levelname)-5s] %(message)s")
    logging.getLogger('swisstext').setLevel(level=logging.DEBUG)
    logging.getLogger('swisstext.tools.pattern_sentence_filter').setLevel(level=logging.WARNING)

    pipeline = Pipeline(
        BsCrawler(),
        PunktSplitter(),
        PatternSentenceFilter(),
        SwigspotLangid(),
        BasicSeedCreator(),
        BasicDecider(),
        ConsoleSaver(),  # MongoSaver(db_name=DB_NAME),
        min_proba=proba
    )

    queue: Queue = PageQueue()

    for u in urlfile:
        if u.startswith("http") and not pipeline.saver.is_url_blacklisted(u):
            queue.put((pipeline.saver.get_page(u.strip(), source=source), 1))

    new_sentences: List[str] = []

    # launch multiple workers
    threads = []
    for i in range(NUM_WORKERS):
        t = threading.Thread(target=PipelineWorker().run, args=(queue, pipeline, new_sentences, MAX_DEPTH))
        t.start()
        threads.append(t)

    # block until all tasks are done
    for t in threads:
        t.join()

    logger.info("Found %d new sentences." % len(new_sentences))

    with open('/tmp/new_sentences.txt', 'w') as f:
        f.write("\n".join(new_sentences))

    if len(new_sentences):
        for seed in pipeline.seeder.generate_seeds(new_sentences):
            print(seed)

    else:
        print("No new sentence found.")

    stop = time.time()
    print("Done. It took {} seconds.".format(stop - start))

if __name__ == "__main__":
    crawl()
