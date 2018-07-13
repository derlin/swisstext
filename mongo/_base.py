from flask_mongoengine import MongoEngine

db = MongoEngine()


def init_db(app, db_name='st1'):
    global db
    app.config['MONGODB_SETTINGS'] = {
        'db': db_name
    }
    db.init_app(app)
