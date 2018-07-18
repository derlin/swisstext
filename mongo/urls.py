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

    @staticmethod
    def blacklist(url):
        murl = MongoURL.objects.with_id(url)
        if murl:
            MongoBlacklist(url=url, date_added=murl.delta_date).save()
            murl.delete()


class MongoBlacklist(Document):
    url = StringField(primary_key=True)
    date_added = DateTimeField(default=datetime.utcnow())
    meta = {'collection': 'blacklist'}

    @staticmethod
    def exists(url) -> bool:
        return MongoBlacklist.objects(url=url).count() == 1
