from flask import Blueprint

from swisstext.frontend.utils.utils import templated

blueprint_index = Blueprint('index', __name__)

@blueprint_index.route('/')
@templated('index.html')
def index():
    return dict()