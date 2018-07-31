from flask_login import UserMixin, LoginManager

from .persistence.models import MongoUser, UserRoles

from .utils.flash import flash_error

login_manager = LoginManager()


def role_required(role=UserRoles.ADMIN):
    from functools import wraps
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            from flask_login import current_user
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            elif not role in current_user.roles:
                flash_error("You don't have permission to access this page.")
                import flask
                if flask.request.referrer and flask.request.referrer.startswith(flask.request.url_root):
                    return flask.redirect(flask.request.referrer)
                return login_manager.unauthorized()
            else:
                return fn(*args, **kwargs)

        return decorated_view

    return wrapper


class User(UserMixin):
    def __init__(self, id, roles):
        self.id = id
        self.roles = roles

    @staticmethod
    def get(*args):
        u = MongoUser.get(*args)
        return User(u.id, u.roles) if u else None
