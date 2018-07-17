from cityhash import CityHash64
from datetime import datetime

from bson import ObjectId
from flask_login import current_user
from flask_mongoengine import *
from mongoengine import EmbeddedDocument

from ._base import db

_user_unknown = ObjectId('0' * 24)


class DialectEntry(EmbeddedDocument):
    user = db.ObjectIdField()
    label = db.StringField()


class MongoSentence(Document):
    id = db.StringField(primary_key=True)
    text = db.StringField()
    url = db.StringField()
    crawl_date = db.DateTimeField(default=datetime.utcnow())
    crawl_proba = db.FloatField()
    validated_by = db.ListField(db.ObjectIdField(), default=[])
    deleted_by = db.ObjectIdField()
    current_dialect = db.StringField()
    current_dialect_count = db.IntField()
    current_dialect_confidence = db.FloatField()
    dialects = db.EmbeddedDocumentListField(DialectEntry, default=[])

    meta = {'collection': 'sentences'}

    @staticmethod
    def exists(text) -> bool:
        return MongoSentence.objects(id=MongoSentence.get_hash(text)).count() == 1

    @staticmethod
    def get_hash(text) -> str:
        return str(CityHash64(text))

    def mark_deleted(self):
        self.deleted_by = current_user.id or _user_unknown
        self.save()

    def unmark_deleted(self):
        # in mongo shell, use $unset:
        # db.sentences.find({_id: xxx}, {$unset: {deleted_by:1}})
        self.deleted_by = None
        self.save()

    def add_label(self, label):
        if not label or current_user.id in [i.user for i in self.dialects]:
            return

        self.dialects.append(DialectEntry(user=current_user.id, label=label))
        if self.current_dialect == label:
            self.current_dialect_count += 1
        else:
            old_count = sum([1 for i in self.dialects if i.label == self.current_dialect])
            new_count = sum([1 for i in self.dialects if i.label == label])

            if new_count > old_count:
                self.current_dialect = label
                self.current_dialect_count = new_count

        self.current_dialect_confidence = self.current_dialect_count / len(self.dialects)
        self.save()
    # _sentences_lock = Lock()
    # _deleted_collection = 'removed'

    # def mark_deleted(self):
    #     with _sentences_lock:
    #         self._move_to(_deleted_collection)
    #
    # def _move_to(self, new_coll):
    #     old_coll = self._collection.name
    #     self.delete()
    #     self.switch_collection(new_coll, False) \
    #         .save() \
    #         .switch_collection(old_coll)
    #
    # @staticmethod
    # def unmark_deleted(id):
    #     with _sentences_lock:
    #         with switch_collection(MongoSentence, _deleted_collection) as RemovedSentence:
    #             sentence = RemovedSentence.objects.with_id(id)
    #             sentence._move_to(MongoSentence._meta['collection'])
