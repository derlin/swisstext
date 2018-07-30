import flask
from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField


class SearchForm(FlaskForm):
    page = HiddenField(default=1)

    apply = SubmitField('Apply')
    reset = SubmitField('Reset')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for i in ['apply', 'reset']:
            # ensure the submit buttons are rendered at the bottom of the form
            self._fields[i] = self._fields.pop(i)
        print(self._unbound_fields)

    def get_page_and_reset(self):
        try:
            page = int(self.page.data)  # get the parameter, then reset
            self.page.data = 1
        except:
            page = 1

        return page

    @classmethod
    def blacklisted_fields(cls):
        return ['csrf_token', 'submit', 'apply']

    @classmethod
    def from_get(cls):
        return cls(flask.request.args)

    @classmethod
    def is_blank(cls):
        return flask.request.method == 'GET' and \
               (len(flask.request.args) == 0 or flask.request.args.get('reset'))

    @classmethod
    def redirect_as_get(cls, endpoint=None, **kwargs):
        args = dict(**flask.request.form)

        if not args.get('reset'):
            # add form arguments to URL only if reset not asked
            [args.pop(k, None) for k in cls.blacklisted_fields()]
            kwargs.update(args)

        if not endpoint:
            # default to current endpoint
            endpoint = flask.request.endpoint
        return flask.redirect(flask.url_for(endpoint, **kwargs))
