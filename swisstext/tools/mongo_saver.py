from swisstext.interfaces import IPageSaver
from swisstext.common.data import Page, PageScore
from swisstext.mongo.data import *
import logging

logger = logging.getLogger(__name__)


class MongoSaver(IPageSaver):

    def __init__(self, db_name='st1'):
        connect(db_name)

    def get_page(self, url: str, **kwargs):
        mu: MongoURL = MongoURL.objects.with_id(url)
        score = PageScore()
        if mu:
            score.count = mu.count
            score.delta_count = mu.delta
            score.delta_date = mu.delta_date
        return Page(url, score, **kwargs)

    def sentence_exists(self, sentence: str):
        return MongoSentence.exists(sentence)

    def save_page(self, page: Page):
        # save sentences first
        for sentence in page.new_sg:
            MongoSentence.create(sentence.text, page.url, sentence.proba)

        # save or update url
        new_count = len(page.new_sg)
        if not MongoURL.exists(page.url) and new_count == 0:
            logger.debug("skipped '%s' (last crawl=%s): no new SG found." % (page, page.score.delta_date))
        else:
            MongoURL.create_or_update(page.url, new_count, source=page.source)
            logger.debug("saved %s (new_count=%d)" % (page, new_count))

    def is_url_blacklisted(self, url: str):
        return MongoBlacklist.exists(url)

    def blacklist_url(self, url: str):
        MongoBlacklist(url=url).save()
