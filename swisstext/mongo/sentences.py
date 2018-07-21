from cityhash import CityHash64
from datetime import datetime

from mongoengine import *

from .generic import Deleted
from .users import MongoUser


class DialectEntry(EmbeddedDocument):
    user = StringField()
    label = StringField()
    date = DateTimeField(default=lambda: datetime.utcnow())


class DialectInfo(EmbeddedDocument):
    count = IntField()
    label = StringField()
    confidence = FloatField()
    labels = EmbeddedDocumentListField(DialectEntry, default=[])
    skipped_by = ListField(MongoUser._id_type(), default=[])

    def add_label(self, uuid, label):
        if not label or uuid in [i.user for i in self.labels]:
            return

        self.labels.append(DialectEntry(user=uuid, label=label))

        if self.label is None:
            self.label = label
            self.count = 1

        elif self.label == label:
            self.label = label
            self.count += 1

        else:
            old_count = sum([1 for i in self.labels if i.label == self.label])
            new_count = sum([1 for i in self.labels if i.label == label])

            if new_count > old_count:
                self.label = label
                self.count = new_count

        self.confidence = self.count / len(self.labels)


class MongoSentence(Document):
    # -- base info
    id = StringField(primary_key=True)
    text = StringField()
    url = StringField()
    # -- crawl info
    crawl_date = DateTimeField(default=lambda: datetime.utcnow())
    crawl_proba = FloatField()
    # -- validation info
    validated_by = ListField(MongoUser._id_type(), default=[])
    deleted = EmbeddedDocumentField(Deleted)
    # -- dialect info
    dialect = EmbeddedDocumentField(DialectInfo)

    meta = {'collection': 'sentences'}

    @staticmethod
    def add_label(obj, uuid, label):
        if isinstance(obj, str): obj = MongoSentence.objects.with_id(obj)
        if isinstance(obj, MongoSentence):
            if obj.dialect is None: obj.dialect = DialectInfo()
            obj.dialect.add_label(uuid, label)
            obj.save()

    @staticmethod
    def exists(text) -> bool:
        return MongoSentence.objects(id=MongoSentence.get_hash(text)).count() == 1

    @staticmethod
    def create(text, url, proba):
        return MongoSentence(id=MongoSentence.get_hash(text), text=text, url=url, crawl_proba=proba)

    @staticmethod
    def get_hash(text) -> str:
        return str(CityHash64(text))

    @staticmethod
    def mark_deleted(obj, uuid, comment=None):
        if isinstance(obj, str): obj = MongoSentence.objects.with_id(obj)
        obj.update(set__deleted=Deleted(by=uuid, comment=comment))

    @staticmethod
    def unmark_deleted(obj):
        # in mongo shell, use $unset:
        # sentences.find({_id: xxx}, {$unset: {deleted_by:1}})
        if isinstance(obj, str): obj = MongoSentence.objects.with_id(obj)
        obj.update(unset__deleted=True)
