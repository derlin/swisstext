from flask_login import UserMixin
from mongoengine import connect

from mongo import MongoUser


class User(UserMixin):
    def __init__(self, id):
        self.id = id

    @staticmethod
    def get(*args):
        u = MongoUser.get(*args)
        return User(u.id) if u else None


def init_db(app, db_name='st1'):
    connect(db_name)
    # global db
    # app.config['MONGODB_SETTINGS'] = {
    #     'db': db_name
    # }
    # db.init_app(app)
