import traceback

import mongoengine
from flask.blueprints import Blueprint

from utils import responses
from utils.errors import AppError
from utils.log import getLogger

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

@errorhandlers.app_errorhandler(IOError)
def handle_db_errors(error):
    _on_error()
    msg = str(error)
    if hasattr(error, 'orig') and hasattr(error.orig, 'msg'):
        msg = error.orig.msg
    return responses.error(
        status_code=500,
        cause=type(error).__name__,  # 'DBError',
        message=msg)


@errorhandlers.app_errorhandler(Exception)
def handle_unknown_errors(error):
    _on_error()
    typ= type(error)
    return responses.error(
        status_code=500,
        cause="%s: %s" % (typ.__module__, typ.__name__),
        message=str(error))


def _on_error():
    # put any logic that should run whatever the error, for example
    # a database rollback.
    # log the error, limiting the stacktrace to 5 calls
    logger.error(traceback.format_exc(limit=5, chain=False))
