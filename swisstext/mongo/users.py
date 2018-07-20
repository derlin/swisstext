import hashlib
from mongoengine import *


class MongoUser(Document):
    # TODO: use a uuid instead ?
    _id_type = StringField

    id = _id_type(primary_key=True)
    password = StringField()

    meta = {'collection': 'users'} # For flask login

    @staticmethod
    def get_hash(password) -> str:
        return hashlib.md5(password.encode()).hexdigest()

    @staticmethod
    def get(uuid: str, password: str = None):
        u = MongoUser.objects.with_id(uuid)
        if u and password is not None:
            return u if MongoUser.get_hash(password) == u.password else None
        return u
