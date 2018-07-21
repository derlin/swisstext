from mongoengine import *
from .generic import CrawlMeta, Source


class MongoSeed(Document):
    id = StringField(primary_key=True)
    source = EmbeddedDocumentField(Source, default=Source())
    count = IntField(default=0)
    search_history = EmbeddedDocumentListField(CrawlMeta, default=[])

    meta = {'collection': 'seeds'}

    @staticmethod
    def get(seed):
        return MongoSeed.objects.with_id(seed)

    @staticmethod
    def create(seed):
        return MongoSeed(id=seed)

    def add_search_history(self, new_links_count):
        self.search_history.append(CrawlMeta(count=new_links_count))
