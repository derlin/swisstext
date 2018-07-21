from datetime import datetime

from mongoengine import *
from .generic import CrawlMeta, Source


class MongoSeed(Document):
    # base info
    id = StringField(primary_key=True)
    source = EmbeddedDocumentField(Source, default=Source())
    date = DateTimeField(default=lambda: datetime.utcnow())
    # seed usage
    count = IntField(default=0)
    delta_date = DateTimeField()
    search_history = EmbeddedDocumentListField(CrawlMeta, default=[])

    meta = {'collection': 'seeds'}

    @staticmethod
    def get(seed):
        return MongoSeed.objects.with_id(seed)

    @staticmethod
    def create(seed):
        return MongoSeed(id=seed)

    def add_search_history(self, new_links_count):
        entry = CrawlMeta(count=new_links_count)
        self.count += new_links_count
        self.delta_date = entry.date
        self.search_history.append(entry)
