import flask
from flask_wtf import FlaskForm
from wtforms import SubmitField


class SearchForm(FlaskForm):

    @classmethod
    def blacklisted_fields(cls):
        return ['csrf_token', 'submit', 'apply']

    @classmethod
    def reset_field(cls) -> str:
        return 'reset'

    @classmethod
    def from_get(cls):
        return cls(flask.request.args)

    @classmethod
    def is_blank(cls, reset_field='reset'):
        return flask.request.method == 'GET' and \
               (len(flask.request.args) == 0 or flask.request.args.get(cls.reset_field()))

    @classmethod
    def redirect_as_get(cls, endpoint=None, **kwargs):
        args = dict(**flask.request.form)

        if not args.get(cls.reset_field()):
            # add form arguments to URL only if reset not asked
            [args.pop(k, None) for k in cls.blacklisted_fields()]
            kwargs.update(args)

        if not endpoint:
            # default to current endpoint
            endpoint = flask.request.endpoint
        return flask.redirect(flask.url_for(endpoint, **kwargs))
