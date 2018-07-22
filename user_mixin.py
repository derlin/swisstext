from flask_login import UserMixin

from persistence.models import MongoUser


class User(UserMixin):
    def __init__(self, id):
        self.id = id

    @staticmethod
    def get(*args):
        u = MongoUser.get(*args)
        return User(u.id) if u else None
