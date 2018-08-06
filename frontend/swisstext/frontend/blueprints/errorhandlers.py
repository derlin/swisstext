import traceback

import mongoengine
from flask.blueprints import Blueprint
from werkzeug.exceptions import NotFound

from swisstext.frontend.utils import responses
from swisstext.frontend.utils.errors import AppError
from swisstext.frontend.utils.log import getLogger

logger = getLogger(__name__)
errorhandlers = Blueprint('error_handlers', __name__)


@errorhandlers.app_errorhandler(AppError)
def handle_app_errors(error):
    _on_error()
    # no need for stacktrace in this case
    logger.error("AppError: cause=%s, message=%s" % (error.cause, error.message))
    return responses.error(
        status_code=error.status_code,
        cause=error.cause,
        message=error.message)


@errorhandlers.app_errorhandler(Exception)
def handle_unknown_errors(error):
    _on_error()

    typ = type(error)
    msg = str(error)
    code = 500

    if hasattr(error, 'orig') and hasattr(error.orig, 'msg'):
        msg = error.orig.msg
    if hasattr(error, 'code'):
        code = error.code

    return responses.error(
        status_code=code,
        cause="%s: %s" % (typ.__module__, typ.__name__),
        message=msg)


def _on_error():
    # put any logic that should run whatever the error, for example
    # a database rollback.
    # log the error, limiting the stacktrace to 5 calls
    logger.error(traceback.format_exc(limit=5, chain=False))
