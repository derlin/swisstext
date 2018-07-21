from mongoengine import connect

from swisstext.mongo import MongoSeed, MongoURL, SourceType, Source
from swisstext.searching.data import Seed
from swisstext.searching.interfaces import ISaver


class MongoSaver(ISaver):
    def __init__(self, host='localhost', port=27017, db='st1', **kwargs):
        connect(db, host=host, port=port)

    def save_seed(self, seed: Seed):
        for url in seed.new_links:
            MongoURL.create(url, Source(SourceType.SEED, seed.query)).save()

        new_links_count = len(seed.new_links)
        s = MongoSeed.get(seed.query) or MongoSeed.create(seed.query)
        s.add_search_history(new_links_count)
        s.count += new_links_count
        s.save()

    def link_exists(self, url: str) -> bool:
        return MongoURL.exists(url)
