# see https://github.com/MongoEngine/flask-mongoengine/issues/309

from swisstext.mongo.abstract import *
from ._base import db


class MongoUser(db.Document, AbstractMongoUser):
    pass


class MongoBlacklist(db.Document, AbstractMongoBlacklist):
    pass


class MongoURL(db.Document, AbstractMongoURL):
    pass


class MongoSeed(db.Document, AbstractMongoSeed):
    pass


class MongoSentence(db.Document, AbstractMongoSentence):
    # here, set a default value so we can accesse s.dialect without fearing a
    # None type error
    dialect = db.EmbeddedDocumentField(DialectInfo, default=lambda: DialectInfo())
