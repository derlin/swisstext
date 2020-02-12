from mongoengine import connect
import logging

from swisstext.mongo.models import MongoSeed, MongoURL, SourceType, Source, MongoBlacklist
from ..data import Seed
from ..interfaces import ISaver

logger = logging.getLogger(__name__)


class MongoSaver(ISaver):
    """
    This :py:class:`~swisstext.cmd.searching.interfaces.ISaver` implementation persists everything to
    a MongoDB database.

    .. seealso::
        :py:mod:`swisstext.mongo`
            Package defining the Mongo collections.
    """

    def __init__(self, host='localhost', port=27017, db='st1', **kwargs):
        connect(db, host=host, port=port)

    def seed_exists(self, seed: str, **kwargs) -> bool:
        return MongoSeed.get(seed) is not None

    def save_seed(self, seed: Seed, was_used: bool):
        s = MongoSeed.get(seed.query) or MongoSeed.create(seed.query)
        if was_used:
            for url in seed.new_links:
                MongoURL.create(url, Source(SourceType.SEED, seed.query)).save()

            new_links_count = len(seed.new_links)
            s.add_search_history(new_links_count)
        s.save()
        logging.info('saved %s' % seed)

    def link_exists(self, url: str) -> ISaver.LinkStatus:
        if MongoBlacklist.exists(url):
            return ISaver.LinkStatus.BLACKLISTED
        else:
            return ISaver.LinkStatus(MongoURL.exists(url))
