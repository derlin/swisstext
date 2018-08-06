# see https://github.com/MongoEngine/flask-mongoengine/issues/309

from swisstext.mongo.abstract import *
from ._base import db


class DialectsWrapper:
    _colors = dict(zip(
        Dialects.keys(),
        ['#DFBBB1', '#94D1D3', '#BCE7FD', '#FFEB3B', '#FFD275', '#9CFFFA', '#ACF39D', '#C1DBB3', '#D5C9DF', '#F2A792']
    ))

    @classmethod
    def choices(cls):
        return cls.items() + [('?', 'No idea')]

    @classmethod
    def items(cls):
        return list(Dialects.items())

    @classmethod
    def description(cls, label):
        return Dialects.get(label, '??')

    @classmethod
    def color(cls, label):
        return cls._colors.get(label, '#FFF')


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
