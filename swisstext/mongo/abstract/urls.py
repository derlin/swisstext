from datetime import datetime
from typing import List

from mongoengine import *

from .generic import Source, CrawlMeta


class AbstractMongoURL(Document):
    id = StringField(primary_key=True)
    source = EmbeddedDocumentField(Source, default=Source())

    crawl_history = EmbeddedDocumentListField(CrawlMeta, default=[])

    count = IntField(default=0)
    delta = IntField(default=0)
    delta_date = DateTimeField(default=None)

    meta = {'collection': 'urls', 'abstract': True}

    @classmethod
    def exists(cls, url) -> bool:
        return cls.objects.with_id(url) is not None

    @classmethod
    def create(cls, url, source=Source()) -> object:
        return cls(id=url, source=source)

    @classmethod
    def get(cls, url) -> object:
        return cls.objects.with_id(url)

    @classmethod
    def get_never_crawled(cls) -> QuerySet:
        return cls.objects(crawl_history__size=0)

    @classmethod
    def try_delete(cls, url: str):
        # remove from url if it exists
        cls.objects(id=url).delete()

    def add_crawl_history(self, new_sg_count):
        meta = CrawlMeta(count=new_sg_count)
        self.crawl_history.append(meta)
        self.count += new_sg_count
        self.delta = meta.count
        self.delta_date = meta.date
        return self  # for chaining


class AbstractMongoBlacklist(Document):
    url = StringField(primary_key=True)
    date_added = DateTimeField(default=lambda: datetime.utcnow())
    source = EmbeddedDocumentField(Source, default=Source())

    meta = {'collection': 'blacklist', 'abstract': True}

    @classmethod
    def exists(cls, url) -> bool:
        return cls.objects.with_id(url) is not None

    @classmethod
    def add_url(cls, url: str, source: Source = None):
        # add it to the blacklist
        cls(
            url=url,
            source=source or Source()
        ).save()
