from flask import Blueprint

from mongo import MongoSentence
import utils.responses as responses

blueprint_api = Blueprint('api', __name__)


@blueprint_api.route('/sentences/<sid>', methods=["DELETE"])
def delete_sentence(sid):
    try:
        sentence = MongoSentence.objects.with_id(sid)
        if sentence:
            sentence.mark_deleted()
            return responses.message("OK")
        else:
            return responses.bad_param("Sentence with id '%s' does not exist." % sid)
    except Exception as e:
        return responses.unknown_server_error(str(e))


@blueprint_api.route('/sentences/<sid>/restore', methods=["GET"])
def restore_sentence(sid):
    try:
        sentence = MongoSentence.objects.with_id(sid)
        if sentence:
            sentence.unmark_deleted()
            return responses.message("OK")
        else:
            return responses.bad_param("Sentence with id '%s' does not exist." % sid)
    except Exception as e:
        return responses.unknown_server_error(str(e))
