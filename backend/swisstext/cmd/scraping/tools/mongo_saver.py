from mongoengine import NotUniqueError

from ..interfaces import ISaver
from ..data import Page, PageScore
from swisstext.mongo.models import *

import logging

logger = logging.getLogger(__name__)


class MongoSaver(ISaver):
    """
    This :py:class:`~swisstext.cmd.scraping.interfaces.ISaver` implementation persists everything to
    a MongoDB database.

    .. seealso::
        :py:mod:`swisstext.mongo`
            Package defining the Mongo collections.
    """

    def __init__(self, db='st1', **kwargs):
        super().__init__()
        get_connection(db, **kwargs)

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
        # save sentences first, ignoring duplicates
        for sentence in page.new_sg:
            try:
                MongoSentence.create(sentence.text, page.url, sentence.proba).save()
            except NotUniqueError:
                # TODO decrease new_sg ?
                logger.warning(f'Exception ignored -- Duplicate sentence found (url: {page.url}.')

        # save text
        text: MongoText = MongoText.create_or_update(page.url, page.text)
        if len(text.urls) > 1:
            logger.info(f'duplicate text found: {text.urls}')
        # save or update url
        new_count = len(page.new_sg)
        mu: MongoURL = MongoURL.get(page.url)
        if mu is None:
            source = Source(SourceType.AUTO, page.parent_url) if page.parent_url else Source()
            mu = MongoURL.create(page.url, source=source)
        mu.add_crawl_history(new_count, hash=text.id)
        # persist
        text.save()
        mu.save()

        logger.info("saved %s (crawled=%d times, new_count=%d)" %
                    (page, len(mu.crawl_history), new_count))

    def is_url_blacklisted(self, url: str):
        return MongoBlacklist.exists(url)

    def blacklist_url(self, url: str, error_message=None, **kwargs):
        MongoURL.try_delete(url)  # remove URL if exists
        if error_message:
            source = Source(SourceType.ERROR, error_message)
        else:
            source = Source(SourceType.AUTO)
        MongoBlacklist.add_url(url, source=source)

    def save_url(self, url: str, parent: str = None):
        MongoURL.create(url, Source(SourceType.AUTO, parent)).save()

    def save_seed(self, seed: str):
        if not MongoSeed.exists(seed):
            MongoSeed.create(seed, Source(SourceType.AUTO)).save()

    @staticmethod
    def url_to_filename(url):
        from urllib.parse import quote
        return quote(url).replace('/', '@')