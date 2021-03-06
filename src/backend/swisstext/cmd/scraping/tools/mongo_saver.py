from threading import Lock

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
        """
        :param db: the database to use
        :param kwargs: may include ``host`` and ``port``
        """
        super().__init__()
        get_connection(db, **kwargs)
        self.lock = Lock()

    def get_page(self, url: str, **kwargs) -> Page:
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
        with self.lock:
            # save sentences first, ignoring duplicates
            for sentence in page.new_sg:
                try:
                    MongoSentence.create(sentence.text, page.url, sentence.proba).save()
                except NotUniqueError:
                    # TODO decrease new_sg ?
                    logger.warning(f'Exception ignored -- Duplicate sentence found (url: {page.url}.')

            # save or update url
            new_count = len(page.new_sg)
            mu: MongoURL = MongoURL.get(page.url)
            if mu is None:
                source = Source(SourceType.AUTO, page.parent_url) if page.parent_url else Source()
                mu = MongoURL.create(page.url, source=source)

            # save raw, unormalized text
            text: MongoText = MongoText.create_or_update(mu.id, page.crawl_results.text)
            if len(text.urls) > 1:
                logger.info(f'duplicate text found: {text.urls}')

            # add crawl history
            mu.add_crawl_history(new_count, hash=text.id, sents_count=page.sentence_count, sg_sents_count=page.sg_count)
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