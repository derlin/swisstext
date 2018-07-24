import hashlib
from mongoengine import *


class UserRoles:
    ADMIN = "admin"
    USER = "user"


class AbstractMongoUser(Document):
    # TODO: use a uuid instead ?
    _id_type = StringField

    id = _id_type(primary_key=True)
    password = StringField()
    roles = ListField(StringField(), default=[UserRoles.ADMIN])

    meta = {'collection': 'users', 'abstract': True}

    @staticmethod
    def get_hash(password) -> str:
        return hashlib.md5(password.encode()).hexdigest()

    @classmethod
    def get(cls, uuid: str, password: str = None):
        u = cls.objects.with_id(uuid)
        if u and password is not None:
            return u if cls.get_hash(password) == u.password else None
        return u
