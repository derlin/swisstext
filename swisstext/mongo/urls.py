from datetime import datetime
from typing import List
from mongoengine import *

from .generic import Source, CrawlMeta, SourceType


class MongoURL(Document):
    id = StringField(primary_key=True)
    source = EmbeddedDocumentField(Source, default=Source())

    crawl_history = EmbeddedDocumentListField(CrawlMeta, default=[])

    count = IntField(default=0)
    delta = IntField(default=0)
    delta_date = DateTimeField(default=None)

    meta = {'collection': 'urls'}

    @staticmethod
    def exists(url) -> bool:
        return MongoURL.objects.with_id(url) is not None

    @staticmethod
    def create(url, source=Source()) -> object:
        return MongoURL(id=url, source=source)

    @staticmethod
    def get(url) -> object:
        return MongoURL.objects.with_id(url)

    @staticmethod
    def get_never_crawled() -> List:
        return MongoURL.objects(crawl_history__size=0)

    def add_crawl_history(self, new_sg_count):
        meta = CrawlMeta(count=new_sg_count)
        self.crawl_history.append(meta)
        self.count += new_sg_count
        self.delta = meta.count
        self.delta_date = meta.date
        return self  # for chaining


class MongoBlacklist(Document):
    url = StringField(primary_key=True)
    date_added = DateTimeField(default=lambda: datetime.utcnow())
    source = EmbeddedDocumentField(Source, default=Source())

    meta = {'collection': 'blacklist'}

    @staticmethod
    def exists(url) -> bool:
        return MongoBlacklist.objects.with_id(url) is not None

    @staticmethod
    def add_url(url: str, source: Source = None):
        # remove from url if it exists
        MongoURL.objects(id=url).delete()
        # add it to the blacklist
        MongoBlacklist(
            url=url,
            source=source or Source()
        ).save()
