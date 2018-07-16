import click
from flask import Flask, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_required, logout_user

import utils.jinja_utils as junja
from blueprints.api import blueprint_api
from blueprints.errorhandlers import errorhandlers
from blueprints.sentence_validation.sentence_validation import blueprint_sentence_validation
from blueprints.users import blueprint_users
from mongo import init_db, User
from utils.utils import templated

app = Flask(__name__)
app.config.update(dict(
    SECRET_KEY="UdIsTiCKlEdGERdbyalDEfEmISTyPo",
    WTF_CSRF_SECRET_KEY="AcelAnFigatMAneyaNteRmatuRAkEY"
))

# flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "users.login"

# bootstrap
bootstrap = Bootstrap(app)

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
app.register_blueprint(blueprint_sentence_validation, url_prefix='/validate')

# -- jinja

@app.route('/')
@templated('index.html')
@login_required
def index():
    return dict()


def init_app():
    init_db(app, db_name='tmp')
    junja.register(app)


@click.command()
@click.option('--debug', '-d', default=False, is_flag=True, help="If set, launch Flask in DEBUG mode.")
@click.option('--host', '-h', default="localhost", help="Listen address.")
@click.option('--port', '-p', default=8080, type=int, help="Listen port.")
def run(debug, host, port):
    if debug:
        app.debug = debug
        app.config['TEMPLATES_AUTO_RELOAD'] = True

    init_app()
    app.url_map.strict_slashes = False
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run()
