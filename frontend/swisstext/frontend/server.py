import click
from flask import Flask, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_required, logout_user, UserMixin

from .utils import jinja_utils as junja
from .blueprints.api import blueprint_api
from .blueprints.errorhandlers import errorhandlers
from .blueprints.labelling import blueprint_labelling
from .blueprints.seeds import blueprint_seeds
from .blueprints.sentences import blueprint_sentences
from .blueprints.urls import blueprint_urls
from .blueprints.validation import blueprint_validation
from .blueprints.users import blueprint_users
from .persistence._base import init_db
from .utils.utils import templated

app = Flask(__name__)
app.config.update(dict(
    SECRET_KEY="UdIsTiCKlEdGERdbyalDEfEmISTyPo",
    WTF_CSRF_SECRET_KEY="AcelAnFigatMAneyaNteRmatuRAkEY"
))

# bootstrap
bootstrap = Bootstrap(app)

from .user_management import User, login_manager
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


#  blueprints
app.register_blueprint(errorhandlers)
app.register_blueprint(blueprint_api, url_prefix='/api')
app.register_blueprint(blueprint_users)
app.register_blueprint(blueprint_seeds, url_prefix='/seeds')
app.register_blueprint(blueprint_validation, url_prefix='/validate')
app.register_blueprint(blueprint_labelling, url_prefix='/label')
app.register_blueprint(blueprint_sentences, url_prefix='/sentences')
app.register_blueprint(blueprint_urls, url_prefix='/urls')


# -- jinja

@app.route('/')
@templated('index.html')
@login_required
def index():
    return dict()


def init_app(debug=False, mongo_host='localhost', mongo_port=27017, db='swisstext'):
    if debug:
        app.debug = debug
        app.config['TEMPLATES_AUTO_RELOAD'] = True
    init_db(app, db_host=mongo_host, db_port=mongo_port, db_name=db)
    junja.register(app)
    app.url_map.strict_slashes = False
    return app

@click.command()
@click.option('--debug/--prod', default=False, is_flag=True, help="If set, launch Flask in DEBUG mode.")
@click.option('--host', '-h', default="localhost", help="Listen address.")
@click.option('--port', '-p', default=8080, type=int, help="Listen port.")
@click.option('--mongo-host', default="localhost", help="Mongo host.")
@click.option('--mongo-port',  default=27017, type=int, help="Mongo port.")
@click.option('--db', default="swisstext", help="Mongo db.")
def run(debug, host, port, mongo_host, mongo_port, db):
    init_app(debug, mongo_host, mongo_port, db)
    app.run(host=host, port=port, debug=debug, threaded=True)