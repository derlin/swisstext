from typing import Dict

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, RadioField, HiddenField, IntegerField
from wtforms import validators

from swisstext.frontend.persistence.models import DialectsWrapper
from swisstext.frontend.utils.search_form import SearchForm

_per_page = 50


def base_mongo_params():
    return dict(
        deleted__exists=False,
        validated_by__0__exists=True,
        dialect__labels__user__ne=current_user.id,
        dialect__skipped_by__ne=current_user.id)


class KeywordsForm(SearchForm):
    search = StringField(
        'search (optional)',
        validators=[validators.Optional(), validators.Length(min=2)]
    )

    dialect = SelectField(
        'dialect',
        choices=DialectsWrapper.choices(),
        validators=[validators.DataRequired()]
    )

    per_page = IntegerField(
        'Results per page',
        default=50,
        validators=[validators.NumberRange(min=1, max=100)]
    )

    save = SubmitField('Save and next')

    def get_mongo_params(self) -> Dict:
        params = base_mongo_params()
        if self.search.data:
            params['text__icontains'] = self.search.data
        return params

    def redirect_after_save(self):
        import flask
        return flask.redirect(
            flask.url_for(
                flask.request.endpoint,
                search=self.search.data,
                dialect=self.dialect.data,
                per_page=self.per_page.data
            ))


# -----------------------------

class OneForm(FlaskForm):
    dialect = RadioField(
        'dialect',
        choices=DialectsWrapper.choices(),
        default='?',
        validators=[validators.DataRequired()]
    )

    sentence_id = HiddenField()
    current_label = HiddenField()

    delete_sentence = SubmitField('x', render_kw=dict(title="Delete sentence completely."))
