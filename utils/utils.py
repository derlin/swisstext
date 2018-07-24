from functools import wraps
import flask


def validate_no_csrf(form):
    return all((form._fields[k].validate(form) for (k, _) in form._unbound_fields))


def url_for_referer(default_endpoint, **default_kwargs):
    ref = flask.request.args.get('ref')
    ref_args = flask.request.args.get('ref_args')
    if ref:
        kwargs = dict((i.split(",") for i in ref_args.split(";"))) if ref_args else {}
        return flask.url_for(ref, **kwargs)
    else:
        return flask.url_for(flask.url_for(default_endpoint, **default_kwargs))


def templated(template=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            template_name = template
            if template_name is None:
                template_name = flask.request.endpoint.replace('.', '/') + '.html'
            ctx = f(*args, **kwargs)
            if ctx is None:
                ctx = {}
            elif not isinstance(ctx, dict):
                return ctx
            return flask.render_template(template_name, **ctx)

        return decorated_function

    return decorator
