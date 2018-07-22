from datetime import datetime

from mongoengine import *
from .generic import CrawlMeta, Source, SourceType


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
    def create(seed, source=Source()):
        return MongoSeed(id=seed, source=source)

    @staticmethod
    def exists(text) -> bool:
        return MongoSeed.objects.with_id(text) is not None

    def add_search_history(self, new_links_count):
        entry = CrawlMeta(count=new_links_count)
        self.count += new_links_count
        self.delta_date = entry.date
        self.search_history.append(entry)

    @staticmethod
    def find_similar(seed):
        import re
        split = re.split('\s+', seed)
        if len(split) == 1:
            return MongoSeed.objects(id_icontains=seed)
        else:
            pattern = "(%s)" % ")|(".join(split)
            return MongoSeed.objects(id=re.compile(pattern, re.IGNORECASE))
