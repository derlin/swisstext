import traceback

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
    return responses.error(
        status_code=500,
        cause='Unknown Error',
        message=str(error))


def _on_error():
    # HIGHLY IMPORTANT: rollback the database transaction to undo all the queries done
    # during this session before the error occurred.
    # This must be done manually because once an error has been handled (here by our custom handlers),
    # it is not propagated further, so app.teardown_XX(exception) receives a None argument --> no way to detect
    # something went wrong !
    #db_abort()
    # log the error, limiting the stacktrace to 5 calls
    logger.error(traceback.format_exc(limit=5, chain=False))
