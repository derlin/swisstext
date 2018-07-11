import logging
import sys
import threading
from queue import Queue

import click

from swisstext.common.page_queue import PageQueue
from swisstext.interfaces import *
from swisstext.page import Page, Sentence
from swisstext.persistance.mongo_saver import MongoSaver
from swisstext.tools.basic_decider import BasicDecider
from swisstext.tools.basic_seed_creator import BasicSeedCreator
from swisstext.tools.bs_crawler import BsCrawler
from swisstext.tools.pattern_sentence_filter import PatternSentenceFilter
from swisstext.tools.punkt_splitter import PunktSplitter
from swisstext.tools.swigspot_langid import SwigspotLangid

logger = logging.getLogger('swisstext.pipeline')


@click.command()
@click.option('-p', '--proba', type=float, default=0.85, help="Min proba for SG")
@click.option('-s', '--source', type=str, default="recrawl")
@click.argument('urlfile', type=click.File('r'))
def go(proba, source, urlfile):
    # one thread, 18 urls = ~ 30 seconds
    import time
    start = time.time()

    MAX_DEPTH = 2
    NUM_WORKERS = 5
    DB_NAME = "tmp"

    logging.basicConfig(stream=sys.stderr, format="[%(name)-15s %(levelname)-5s] %(message)s")
    logging.getLogger('swisstext').setLevel(level=logging.DEBUG)
    logging.getLogger('swisstext.tools.pattern_sentence_filter').setLevel(level=logging.WARNING)

    downloader: ICrawler = BsCrawler()
    splitter: ISplitter = PunktSplitter()
    filter: ISentenceFilter = PatternSentenceFilter()
    langid: ISgDetector = SwigspotLangid()
    genSeeds: ISeedCreator = BasicSeedCreator()
    saver: IPageSaver = MongoSaver(db_name=DB_NAME)
    decider: IDecider = BasicDecider()

    queue: Queue = PageQueue()
    lock: threading.Lock = threading.Lock()

    for u in urlfile:
        if u.startswith("http") and not saver.is_url_blacklisted(u):
            queue.put((saver.get_page(u.strip(), source=source), 1))

    new_sentences: List[str] = []

    def worker():
        while not queue.empty():
            (page, page_depth) = queue.get()
            logger.debug("Processing: %s (depth=%d)" % (page.url, page_depth))
            if page_depth > MAX_DEPTH:
                logging.info(
                    "reached max depth for recursive scraping (still %d links in queue). Exiting." % queue.qsize())
                break

            if decider.should_page_be_crawled(page):
                try:
                    page.crawl_results = downloader.crawl(page.url)
                    splitted: List[str] = splitter.split(page.crawl_results.text)
                    sentences: List[str] = filter.filter(splitted)
                    page.sentence_count = 0

                    for (s, p) in zip(sentences, langid.predict(sentences)):
                        page.sentence_count += 1
                        if p >= proba:
                            page.sg_count += 1
                            if not saver.sentence_exists(s):
                                page.new_sg.append(Sentence(s, p))

                    if page.new_sg:
                        with lock:
                            new_sentences.extend(page.new_sg)

                    if decider.should_url_be_blacklisted(page):
                        logger.info("blacklisting %s" % page.url)
                        saver.blacklist_url(page.url)

                    else:
                        saver.save_page(page)
                        if page_depth < MAX_DEPTH and decider.should_children_be_crawled(page):
                            added_children = 0
                            for l in page.crawl_results.links:
                                if not saver.is_url_blacklisted(l):
                                    queue.put((Page(l, source=page.url), page_depth + 1))
                                    added_children += 1
                            logger.debug("%s: added %d child URLs" % (page.url, added_children))

                except Exception as e:

                    if not isinstance(e, ICrawler.CrawlError):
                        logger.exception(e)
            else:
                logger.debug("Skipped '%s'" % page.url)
        queue.task_done()

    # launch multiple workers
    threads = []
    for i in range(NUM_WORKERS):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    # block until all tasks are done
    for t in threads:
        t.join()

    logger.info("Found %d new sentences." % len(new_sentences))

    with open('/tmp/new_sentences.txt', 'w') as f:
        f.write("\n".join(new_sentences))

    if len(new_sentences):
        for seed in genSeeds.generate_seeds(new_sentences):
            print(seed)

    else:
        print("No new sentence found.")

    stop = time.time()
    print("Done. It took {} seconds.".format(stop - start))


if __name__ == "__main__":
    go()
