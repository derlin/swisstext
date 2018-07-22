# see https://github.com/MongoEngine/flask-mongoengine/issues/309

from mongo.abstract import *
from persistence._base import db


class MongoUser(db.Document, AbstractMongoUser):
    pass


class MongoBlacklist(db.Document, AbstractMongoBlacklist):
    pass


class MongoURL(db.Document, AbstractMongoURL):
    pass


class MongoSeed(db.Document, AbstractMongoSeed):
    pass


class MongoSentence(db.Document, AbstractMongoSentence):
    pass
