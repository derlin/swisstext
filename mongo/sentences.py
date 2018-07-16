from cityhash import CityHash64
from datetime import datetime

from bson import ObjectId
from flask_login import current_user
from flask_mongoengine import *

from ._base import db

_user_unknown = ObjectId('0' * 24)


class MongoSentence(Document):
    id = db.StringField(primary_key=True)
    text = db.StringField()
    url = db.StringField()
    crawl_date = db.DateTimeField(default=datetime.utcnow())
    crawl_proba = db.FloatField()
    validation = db.ListField(db.ObjectIdField(), default=[])
    deleted_by = db.ObjectIdField()
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
