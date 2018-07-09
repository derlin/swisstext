from typing import List

from swisstext.interfaces import IPageSaver
from swisstext.page import Page, PageScore
from mongoengine import *
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MongoSaver(IPageSaver):

    def __init__(self):
        connect('st1')

    def get_page(self, url: str):
        mu: MongoURL = MongoURL.objects.with_id(url)
        score = PageScore()
        if mu:
            score.count = mu.count
            score.delta_count = mu.delta
            score.delta_date = mu.delta_date
        return Page(url, mu)

    def sentence_exists(self, sentence: str):
        return MongoSentence.exists(sentence)

    def save_page(self, page: Page) -> List[str]:
        # save sentences first
        new_sentences = []
        for (sentence, proba) in page.sg:
            if not self.sentence_exists(sentence):
                MongoSentence.create(sentence, page.url, proba)
                new_sentences.append(sentence)

        # save or update url
        new_count = len(new_sentences)
        if not MongoURL.exists(page.url) and new_count == 0:
            logger.debug("skipped '%s': no SG found.")
        else:
            MongoURL.create_or_update(page.url, new_count)
            logger.debug("Saved [cnt=%-3d] %s" % (new_count, page.url))
        return new_sentences


# ----------------- URL

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
            logging.debug("Updated url '%s'" % url)
            mu = MongoURL.objects.with_id(url)
        else:
            logging.debug("Creating new url '%s'" % url)
            mu = MongoURL(id=url)
            mu.count = count

        meta = MongoCrawlMeta(count=count)
        mu.crawl_history.append(meta)
        mu.delta = meta.count
        mu.delta_date = meta.date

        mu.save()


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
