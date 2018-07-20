from swisstext.scraping.interfaces import IPageSaver
from swisstext.scraping.common.data import Page, PageScore
from swisstext.mongo import *
from mongoengine import connect
import logging

logger = logging.getLogger(__name__)


class MongoSaver(IPageSaver):

    def __init__(self, host='localhost', port=27017, db='st1', **kwargs):
        super().__init__()
        connect(db, host=host, port=port)

    def get_page(self, url: str, **kwargs):
        mu: MongoURL = MongoURL.get(url)
        score: PageScore = None

        if mu:
            score = PageScore(
                count=mu.count,
                delta_count=mu.delta,
                delta_date=mu.delta_date)

        return Page(url, score=score, **kwargs)

    def sentence_exists(self, sentence: str):
        return MongoSentence.exists(sentence)

    def save_page(self, page: Page):
        # save sentences first
        for sentence in page.new_sg:
            MongoSentence.create(sentence.text, page.url, sentence.proba).save()
        # save or update url
        new_count = len(page.new_sg)
        mu: MongoURL = MongoURL.get(page.url)
        if mu is None:
            source = Source(SourceType.AUTO, page.parent_url) if page.parent_url else Source()
            mu = MongoURL.create(page.url, source=source)
        mu.add_crawl_history(new_count)
        mu.save()

        logger.debug("saved %s (crawled=%d times, new_count=%d)" %
                     (page, len(mu.crawl_history), new_count))

    def is_url_blacklisted(self, url: str):
        return MongoBlacklist.exists(url)

    def blacklist_url(self, url: str):
        MongoBlacklist.add_url(url, source=Source(SourceType.AUTO))
