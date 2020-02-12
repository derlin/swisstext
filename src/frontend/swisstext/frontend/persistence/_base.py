from flask_mongoengine import MongoEngine

db = MongoEngine()


def init_db(app, db_name, db_host='localhost', db_port=27017):
    # connect(db_name)
    app.logger.info("Connecting to mongo (host={}:{}, db={})".format(db_host, 27017, db_name))
    global db
    app.config['MONGODB_SETTINGS'] = {
        'host': db_host,
        'port': db_port,
        'db': db_name,
        'connect': False,
    }
    db.init_app(app)
