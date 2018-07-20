from mongoengine import *
from datetime import datetime

from .users import MongoUser

class SourceType:
    UNKNOWN = "unknown"
    USER = "user"
    AUTO = "auto"


class Source(EmbeddedDocument):
    type_ = StringField(db_field='type', default=SourceType.UNKNOWN)
    extra = StringField()

class CrawlMeta(EmbeddedDocument):
    date = DateTimeField(default=datetime.utcnow())
    count = IntField(default=0)


class Deleted(EmbeddedDocument):
    by = MongoUser._id_type()
    comment = StringField()
    date = DateTimeField(default=datetime.utcnow())
