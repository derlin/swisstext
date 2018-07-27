from flask_mongoengine import MongoEngine

db = MongoEngine()


def init_db(app, db_name, db_host='localhost'):
    # connect(db_name)
    app.logger.info("Connecting to mongo (host={}:{}, db={})".format(db_host, 27017, db_name))
    global db
    app.config['MONGODB_SETTINGS'] = {
        'host': db_host,
        'db': db_name
    }
    db.init_app(app)
