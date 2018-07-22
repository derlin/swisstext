from datetime import datetime

from mongoengine import *
from .generic import CrawlMeta, Source, Deleted


class AbstractMongoSeed(Document):
    # base info
    id = StringField(primary_key=True)
    source = EmbeddedDocumentField(Source, default=Source())
    date = DateTimeField(default=lambda: datetime.utcnow())
    # seed usage
    count = IntField(default=0)
    delta_date = DateTimeField()
    search_history = EmbeddedDocumentListField(CrawlMeta, default=[])
    # deletion
    deleted = EmbeddedDocumentField(Deleted)

    meta = {'collection': 'seeds', 'abstract': True}

    @classmethod
    def get(cls, seed):
        return cls.objects.with_id(seed)

    @classmethod
    def create(cls, seed, source=Source()):
        return cls(id=seed, source=source)

    @classmethod
    def exists(cls, text) -> bool:
        return cls.objects.with_id(text) is not None

    def add_search_history(self, new_links_count):
        entry = CrawlMeta(count=new_links_count)
        self.count += new_links_count
        self.delta_date = entry.date
        self.search_history.append(entry)

    @classmethod
    def find_similar(cls, seed):
        import re
        split = re.split('\s+', seed)
        if len(split) == 1:
            return cls.objects(id__icontains=seed)
        else:
            pattern = "(%s)" % ")|(".join(split)
            return cls.objects(id=re.compile(pattern, re.IGNORECASE))
