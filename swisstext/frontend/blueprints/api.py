from flask import Blueprint
from flask_login import current_user, login_required

from swisstext.frontend.persistence.models import MongoSentence
import swisstext.frontend.utils.responses as responses

blueprint_api = Blueprint('api', __name__)


@blueprint_api.route('/sentences/<sid>', methods=["DELETE"])
@login_required
def delete_sentence(sid):
    try:
        MongoSentence.mark_deleted(sid, current_user.id)
        return responses.message("'%s' deleted." % sid)
    except Exception as e:
        return responses.unknown_server_error(str(e))


@blueprint_api.route('/sentences/<sid>/restore', methods=["GET"])
@login_required
def restore_sentence(sid):
    try:
        MongoSentence.unmark_deleted(sid)
        return responses.message("'%s' undeleted." % sid)
    except Exception as e:
        return responses.unknown_server_error(str(e))

@blueprint_api.route('/sentences/<sid>/validate', methods=["GET"])
@login_required
def validate_sentence(sid):
    try:
        MongoSentence.objects.with_id(sid).update(add_to_set__validated_by=current_user.id)
        return responses.message("'%s' validated." % sid)
    except Exception as e:
        return responses.unknown_server_error(str(e))