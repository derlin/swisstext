from flask import Blueprint, redirect, url_for
from flask import request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired, Length

from mongo import MongoSentence
from utils.utils import templated

blueprint_labelling = Blueprint('labelling', __name__, template_folder='.')

_per_page = 50


class SearchForm(FlaskForm):
    search = StringField(
        'search',
        validators=[DataRequired(), Length(min=2)])
    dialect = SelectField(
        'dialect',
        choices=[('', '-- ?? --'), ('be', 'Bernese'), ('arg', 'Argau')], # TODO
        validators=[DataRequired()])

    submit = SubmitField('Search')
    save = SubmitField('Save and next')


@blueprint_labelling.route('', methods=['GET', 'POST'])
@login_required
@templated('labelling.html')
def add_labels():
    form = SearchForm()
    sentences = []
    has_results = False
    if request.method == 'POST':
        if form.validate():

            if form.save.data:
                for k, v in request.form.items():
                    if k.startswith('sentence-'):
                        MongoSentence.objects.with_id(k[9:]).add_label(v)

            sentences = MongoSentence.objects(
                text__contains=form.search.data,
                dialects__user__ne=current_user.id
            ).limit(_per_page)
            has_results = True

    return dict(form=form, sentences=sentences, has_results=has_results)
