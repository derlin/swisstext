from flask_mongoengine import *
from ._base import db
from datetime import datetime
from cityhash import CityHash64

class MongoSentence(Document):
    id = db.StringField(primary_key=True)
    text = db.StringField()
    url = db.StringField()
    crawl_date = db.DateTimeField(default=datetime.utcnow())
    crawl_proba = db.FloatField()

    meta = {'collection': 'sentences'}

    @staticmethod
    def exists(text) -> bool:
        return MongoSentence.objects(id=MongoSentence.get_hash(text)).count() == 1

    @staticmethod
    def get_hash(text) -> str:
        return str(CityHash64(text))