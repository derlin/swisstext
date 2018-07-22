from mongoengine import *
from datetime import datetime

from .users import AbstractMongoUser


class SourceType:
    UNKNOWN = "unknown"
    USER = "user"
    AUTO = "auto"
    SEED = "seed"


class Source(EmbeddedDocument):
    type_ = StringField(db_field='type', default=SourceType.UNKNOWN)
    extra = StringField()


class CrawlMeta(EmbeddedDocument):
    date = DateTimeField(default=lambda: datetime.utcnow())
    count = IntField(default=0)


class Deleted(EmbeddedDocument):
    by = AbstractMongoUser._id_type()
    comment = StringField()
    date = DateTimeField(default=lambda: datetime.utcnow())
