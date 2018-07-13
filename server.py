from flask import Flask, render_template, request
import click
from flask_login import LoginManager

from blueprints.errorhandlers import errorhandlers
from blueprints.api import blueprint_api
from blueprints.users import blueprint_users
from mongo import MongoSentence, init_db, User
from utils.utils import templated
import utils.jinja_utils as junja

app = Flask(__name__)
app.config.update(dict(
    SECRET_KEY="UdIsTiCKlEdGERdbyalDEfEmISTyPo",
    WTF_CSRF_SECRET_KEY="AcelAnFigatMAneyaNteRmatuRAkEY"
))

# flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


#  blueprints
app.register_blueprint(errorhandlers)
app.register_blueprint(blueprint_api, url_prefix='/api')
app.register_blueprint(blueprint_users)


# -- jinja

@app.route('/')
@templated('index.html')
def index():
    page = int(request.args.get('page', 1))
    return dict(sentences=MongoSentence.objects.paginate(page=page, per_page=50))


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
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run()
