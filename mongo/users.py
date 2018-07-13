import hashlib
import uuid

from bson import ObjectId
from flask_login import UserMixin, login_manager

from mongo._base import db


class User(UserMixin, db.Document):
    name = db.StringField(unique=True)
    password = db.StringField()

    meta = {'collection': 'users'}

    @staticmethod
    def get_hash(password) -> str:
        return hashlib.md5(password.encode()).hexdigest()

    def check_password(self, password) -> bool:
        return User.get_hash(password) == self.password

    @staticmethod
    def get(uuid: ObjectId):
        return User.objects.with_id(uuid)

    @staticmethod
    def from_name(name: str, password: str = None):
        u = User.objects(name=name).first()
        if u and password:
            return u if u.check_password(password) else None
        return u
