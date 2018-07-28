from cityhash import CityHash64
from datetime import datetime

from mongoengine import *

from .generic import Deleted
from .users import AbstractMongoUser


class DialectEntry(EmbeddedDocument):
    user = StringField()
    label = StringField()
    date = DateTimeField(default=lambda: datetime.utcnow())


class DialectInfo(EmbeddedDocument):
    count = IntField()
    label = StringField()
    confidence = FloatField()
    labels = EmbeddedDocumentListField(DialectEntry, default=[])
    skipped_by = ListField(AbstractMongoUser._id_type(), default=[])

    def remove_label(self, uuid):
        if self.labels:
            self.labels = [l for l in self.labels if l.user != uuid]
            self._recompute_label()

    def add_label(self, uuid, label):
        if label and uuid not in [i.user for i in self.labels]:
            self.labels.append(DialectEntry(user=uuid, label=label))
            self._recompute_label()

    def _recompute_label(self):
        if self.labels:
            sums = {}
            for l in self.labels:
                sums.setdefault(l.label, 0)
                sums[l.label] += 1
            self.label, self.count = sorted(sums.items(), key=lambda t: -t[1])[0]
            self.confidence = self.count / len(self.labels)
        else:
            self.label = None
            self.count, self.confidence = 0, .0


class AbstractMongoSentence(Document):
    # -- base info
    id = StringField(primary_key=True)
    text = StringField()
    url = StringField()
    # -- crawl info
    date_added = DateTimeField(default=lambda: datetime.utcnow())
    crawl_proba = FloatField()
    # -- validation info
    validated_by = ListField(AbstractMongoUser._id_type(), default=[])
    deleted = EmbeddedDocumentField(Deleted)
    # -- dialect info
    dialect = EmbeddedDocumentField(DialectInfo)

    meta = {'collection': 'sentences', 'abstract': True}

    @classmethod
    def add_label(cls, obj, uuid, label):
        if isinstance(obj, str): obj = cls.objects.with_id(obj)
        if isinstance(obj, cls):
            if obj.dialect is None: obj.dialect = DialectInfo()
            obj.dialect.add_label(uuid, label)
            obj.save()

    @classmethod
    def remove_label(cls, obj, uuid):
        if isinstance(obj, str): obj = cls.objects.with_id(obj)
        if isinstance(obj, cls):
            obj.dialect.remove_label(uuid)
            obj.save()

    @classmethod
    def exists(cls, text) -> bool:
        return cls.objects(id=cls.get_hash(text)).count() == 1

    @classmethod
    def create(cls, text, url, proba):
        return cls(id=cls.get_hash(text), text=text, url=url, crawl_proba=proba)

    @staticmethod
    def get_hash(text) -> str:
        return str(CityHash64(text))

    @classmethod
    def mark_deleted(cls, obj, uuid, comment=None):
        if isinstance(obj, str): obj = cls.objects.with_id(obj)
        obj.update(set__deleted=Deleted(by=uuid, comment=comment))

    @classmethod
    def unmark_deleted(cls, obj):
        # in mongo shell, use $unset:
        # sentences.find({_id: xxx}, {$unset: {deleted_by:1}})
        if isinstance(obj, str): obj = cls.objects.with_id(obj)
        obj.update(unset__deleted=True)
