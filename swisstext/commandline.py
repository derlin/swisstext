import logging
import sys
import threading
from queue import Queue

import click

from swisstext.common.page_queue import PageQueue
from swisstext.config import Config
from swisstext.interfaces import *
from swisstext.pipeline import PipelineWorker

logger = logging.getLogger('swisstext.pipeline')


@click.command()
@click.option('-s', '--source', type=str, default="recrawl")
@click.option('-c', '--config', type=click.Path(dir_okay=False), default=None)
@click.argument('urlfile', type=click.File('r'))
def crawl(source, config, urlfile):
    config = Config(config)

    # one thread, 18 urls = ~ 30 seconds
    import time
    start = time.time()

    MAX_DEPTH = config.options.crawl_depth
    NUM_WORKERS = config.options.num_workers
    DB_NAME = config.options.mongo['db']

    logging.basicConfig(stream=sys.stderr, format="[%(name)-15s %(levelname)-5s] %(message)s")
    logging.getLogger('swisstext').setLevel(level=logging.DEBUG)
    logging.getLogger('swisstext.tools.pattern_sentence_filter').setLevel(level=logging.WARNING)

    pipeline = config.create_pipeline()

    queue: Queue = PageQueue()

    for u in urlfile:
        if u.startswith("http") and not pipeline.saver.is_url_blacklisted(u):
            queue.put((pipeline.saver.get_page(u.strip(), source=source), 1))

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

    if len(new_sentences):
        for seed in pipeline.seeder.generate_seeds(new_sentences):
            print(seed)

    else:
        print("No new sentence found.")

    stop = time.time()
    print("Done. It took {} seconds.".format(stop - start))


if __name__ == "__main__":
    crawl()
