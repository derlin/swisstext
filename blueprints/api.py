from flask import Blueprint
from flask_login import current_user

from persistence.models import MongoSentence
import utils.responses as responses

blueprint_api = Blueprint('api', __name__)


@blueprint_api.route('/sentences/<sid>', methods=["DELETE"])
def delete_sentence(sid):
    try:
        MongoSentence.mark_deleted(sid, current_user.id)
        return responses.message("'%s' deleted." % sid)
    except Exception as e:
        return responses.unknown_server_error(str(e))


@blueprint_api.route('/sentences/<sid>/restore', methods=["GET"])
def restore_sentence(sid):
    try:
        MongoSentence.unmark_deleted(sid)
        return responses.message("'%s' undeleted." % sid)
    except Exception as e:
        return responses.unknown_server_error(str(e))
