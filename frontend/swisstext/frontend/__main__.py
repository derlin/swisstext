from flask import Flask, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_login import login_required, logout_user

from swisstext.frontend.utils import jinja_utils as junja
from swisstext.frontend.blueprints import *

from swisstext.frontend.persistence._base import init_db
from swisstext.frontend.utils.utils import templated

# === default arguments

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = '8000'
DEFAULT_MONGO_HOST = DEFAULT_HOST
DEFAULT_MONGO_PORT = 27017
DEFAULT_MONGO_DB = 'swisstext'

# === app

app = Flask(__name__)
app.config.update(dict(
    SECRET_KEY="UdIsTiCKlEdGERdbyalDEfEmISTyPo",
    WTF_CSRF_SECRET_KEY="AcelAnFigatMAneyaNteRmatuRAkEY"
))

bootstrap = Bootstrap(app)

# === users and login
from swisstext.frontend.user_management import User, login_manager
login_manager.init_app(app)
login_manager.login_view = "users.login"

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('users.login'))


# === blueprints
app.register_blueprint(errorhandlers)
app.register_blueprint(blueprint_api, url_prefix='/api')
app.register_blueprint(blueprint_users)
app.register_blueprint(blueprint_seeds, url_prefix='/seeds')
app.register_blueprint(blueprint_validation, url_prefix='/validate')
app.register_blueprint(blueprint_labelling, url_prefix='/label')
app.register_blueprint(blueprint_sentences, url_prefix='/sentences')
app.register_blueprint(blueprint_urls, url_prefix='/urls')


# === index

@app.route('/')
@templated('index.html')
@login_required
def index():
    return dict()

# === setup

def init_app(debug=False, mongo_host='localhost', mongo_port=27017, db='swisstext', **kwargs):
    # an init method is necessary to use gunicorn
    if debug:
        app.debug = debug
        app.config['TEMPLATES_AUTO_RELOAD'] = True
    init_db(app, db_host=mongo_host, db_port=mongo_port, db_name=db)
    junja.register(app)
    app.url_map.strict_slashes = False
    return app


def main():
    # a method is necessary for setuptools entrypoints
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help='run in debug mode', action='store_true')
    parser.add_argument('-t', '--threaded', help='activate threading', action='store_true')
    parser.add_argument('--host', default=DEFAULT_HOST, type=str)
    parser.add_argument('-p', '--port', default=DEFAULT_PORT, type=str)
    parser.add_argument('--mongo-host', default=DEFAULT_MONGO_HOST, help="Mongo host.")
    parser.add_argument('--mongo-port', default=DEFAULT_MONGO_PORT, type=int, help="Mongo port.")
    parser.add_argument('--db', default="swisstext", help="Mongo db.")

    args = parser.parse_args()
    init_app(**vars(args)).run(host=args.host, port=args.port, debug=args.debug, threaded=args.threaded)

if __name__ == "__main__":
    # this lets the module be called using python -m swisstext.frontend
    main()