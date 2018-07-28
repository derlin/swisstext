from .abstract import *


def get_connection(db='st1', host='localhost', port=27017, **kwargs):
    from mongoengine import connect
    return connect(db, host=host, port=port)


class MongoUser(AbstractMongoUser):
    pass


class MongoBlacklist(AbstractMongoBlacklist):
    pass


class MongoURL(AbstractMongoURL):
    pass


class MongoSeed(AbstractMongoSeed):
    pass


class MongoSentence(AbstractMongoSentence):
    pass
