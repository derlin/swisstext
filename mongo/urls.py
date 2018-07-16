from datetime import datetime

from mongoengine import StringField, IntField, DateTimeField, EmbeddedDocumentListField, EmbeddedDocument, Document


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


class MongoBlacklist(Document):
    url = StringField(primary_key=True)
    date_added = DateTimeField(default=datetime.utcnow())
    meta = {'collection': 'blacklist'}

    @staticmethod
    def exists(url) -> bool:
        return MongoBlacklist.objects(url=url).count() == 1
