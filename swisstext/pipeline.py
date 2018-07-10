import sys
from queue import Queue
from typing import Iterator

from swisstext.common.page_queue import PageQueue
from swisstext.interfaces import *
from swisstext.persistance.mongo_saver import MongoSaver

from swisstext.page import Page, Sentence
from swisstext.tools.basic_decider import BasicDecider
from swisstext.tools.basic_seed_creator import BasicSeedCreator
from swisstext.tools.pattern_sentence_filter import PatternSentenceFilter
from swisstext.tools.swigspot_langid import SwigspotLangid
from swisstext.tools.punkt_splitter import PunktSplitter
from swisstext.tools.bs_crawler import BsCrawler

import logging

import click

logger = logging.getLogger('swisstext.pipeline')


@click.command()
@click.option('-p', '--proba', type=float, default=0.85, help="Min proba for SG")
@click.option('-s', '--source', type=str, default="recrawl")
@click.argument('urlfile', type=click.File('r'))
def go(proba, source, urlfile):
    import time
    start = time.time()

    MAX_DEPTH = 3

    logging.basicConfig(stream=sys.stderr, format="[%(name)-15s %(levelname)-5s] %(message)s")
    logging.getLogger('swisstext').setLevel(level=logging.DEBUG)
    logging.getLogger('swisstext.tools.pattern_sentence_filter').setLevel(level=logging.WARNING)

    downloader: ICrawler = BsCrawler()
    splitter: ISplitter = PunktSplitter()
    filter: ISentenceFilter = PatternSentenceFilter()
    langid: ISgDetector = SwigspotLangid()
    genSeeds: ISeedCreator = BasicSeedCreator()
    saver: IPageSaver = MongoSaver()
    decider: IDecider = BasicDecider()

    queue: Queue = PageQueue()

    for u in urlfile:
        if u.startswith("http") and not saver.is_url_blacklisted(u):
            queue.put((saver.get_page(u.strip(), source=source), 1))

    new_sentences: List[str] = []

    while not queue.empty():
        (page, page_depth) = queue.get()
        logger.debug("Processing: %s (depth=%d)" % (page.url, page_depth))
        if page_depth > MAX_DEPTH:
            logging.info("reached max depth for recursive scraping (still %d links in queue). Exiting." % queue.qsize())
            break

        if decider.should_page_be_crawled(page):
            try:
                page.crawl_results = downloader.crawl(page.url)
                splitted: List[str] = splitter.split(page.crawl_results.text)
                sentences: List[str] = filter.filter(splitted)
                page.sentence_count = len(sentences)

                for (s, p) in zip(sentences, langid.predict(sentences)):
                    if p >= proba:
                        page.sg_count += 1
                        if not saver.sentence_exists(s):
                            page.new_sg.append(Sentence(s, p))
                            new_sentences.append(s)

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
                    logger.error(e)
        else:
            logger.debug("Skipped '%s'" % page.url)

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
