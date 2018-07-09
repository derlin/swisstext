import sys
from typing import List

from swisstext.persistance.mongo_saver import MongoSaver

from swisstext.page import Page
from swisstext.tools.basic_seed_creator import BasicSeedCreator
from swisstext.tools.pattern_sentence_filter import PatternSentenceFilter
from swisstext.tools.swigspot_langid import SwigspotLangid
from swisstext.tools.punkt_splitter import PunktSplitter
from swisstext.tools.bs_crawler import BsCrawler

import logging

import click
import mongoengine

logger = logging.getLogger(__name__)


@click.command()
@click.option('-p', '--proba', type=float, default=0.85, help="Min proba for SG")
@click.argument('urlfile', type=click.File('r'))
def go(proba, urlfile):
    logging.basicConfig(stream=sys.stderr, format="[%(name)-15s %(levelname)-5s] %(message)s")
    logging.getLogger('swisstext').setLevel(level=logging.DEBUG)

    downloader = BsCrawler()
    splitter = PunktSplitter()
    filter = PatternSentenceFilter()
    langid = SwigspotLangid()
    genSeeds = BasicSeedCreator()
    saver = MongoSaver()

    langid.predict([])

    pages = [Page(u.strip()) for u in urlfile]

    new_sentences = []

    for page in pages:
        page.crawl_results = downloader.crawl(page.url)
        sentences = filter.filter(splitter.split(page.crawl_results.text))
        page.sg = [(s, p) for (s, p) in zip(sentences, langid.predict(sentences)) if p >= proba]
        new_sentences.extend(saver.save_page(page))

    logger.info("Found %d new sentences." % len(new_sentences))
    if len(new_sentences):
        for seed in genSeeds.generate_seeds(new_sentences):
            print(seed)

    else:
        print("No new sentence found.")


if __name__ == "__main__":
    go()
