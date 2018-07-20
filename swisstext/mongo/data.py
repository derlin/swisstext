from mongoengine import *
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ----------------- URL

class MongoBlacklist(Document):
    url = StringField(primary_key=True)
    date_added = DateTimeField(default=datetime.utcnow())
    meta = {'collection': 'blacklist'}

    @staticmethod
    def exists(url) -> bool:
        return MongoBlacklist.objects(url=url).count() == 1


class MongoCrawlMeta(EmbeddedDocument):
    date = DateTimeField(default=datetime.utcnow())
    count = IntField(default=0)


class MongoURL(Document):
    id = StringField(primary_key=True)
    source = StringField(default=None)

    count = IntField(default=0)
    delta = IntField(default=0)
    delta_date = DateTimeField(default=None)

    crawl_history = EmbeddedDocumentListField(MongoCrawlMeta, default=[])

    meta = {'collection': 'urls'}

    @staticmethod
    def exists(url) -> bool:
        return MongoURL.objects(id=url).count() > 0

    @staticmethod
    def create_or_update(url, count, source=None):
        if MongoURL.exists(url):
            logger.debug("Updated url '%s'" % url)
            mu = MongoURL.objects.with_id(url)
        else:
            logger.debug("Creating new url '%s'" % url)
            mu = MongoURL(id=url, source=source)
            mu.count = count

        meta = MongoCrawlMeta(count=count)
        mu.crawl_history.append(meta)
        mu.delta = meta.count
        mu.delta_date = meta.date

        mu.save()
        return mu


# ----------- Sentence

from cityhash import CityHash64


class MongoSentence(Document):
    id = StringField(primary_key=True)
    text = StringField()
    url = StringField()
    crawl_date = DateTimeField(default=datetime.utcnow())
    crawl_proba = FloatField()

    meta = {'collection': 'sentences'}

    @staticmethod
    def exists(text) -> bool:
        return MongoSentence.objects(id=MongoSentence.get_hash(text)).count() == 1

    @staticmethod
    def get_hash(text) -> str:
        return str(CityHash64(text))

    @staticmethod
    def create(text, url, proba):
        s = MongoSentence(text=text, url=url, crawl_proba=proba)
        s.id = MongoSentence.get_hash(text)
        s.save()
