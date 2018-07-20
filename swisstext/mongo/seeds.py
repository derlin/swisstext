from mongoengine import *
from .generic import CrawlMeta, Source


class MongoSeed(Document):
    id = StringField(primary_key=True)
    source = EmbeddedDocumentField(Source, default=Source())
    count = IntField(default=0)
    search_history = EmbeddedDocumentListField(CrawlMeta, default=[])

    meta = {'collection': 'seeds'}
