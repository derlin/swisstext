from flask import Blueprint

from utils.utils import templated
from mongo import MongoSentence
import utils.responses as responses

blueprint_api = Blueprint('api', __name__)


@blueprint_api.route('/sentences/<sid>', methods=["DELETE"])
def index(sid):
    try:
        MongoSentence.objects.with_id(sid).delete()
        return responses.message("OK")
    except Exception as e:
        return responses.unknown_server_error(str(e))
