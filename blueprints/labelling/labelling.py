from flask import Blueprint, redirect, url_for
from flask import request
from flask_login import login_required, current_user

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms import validators

from mongo import MongoSentence
from utils.flash import flash_success
from utils.utils import templated, validate_no_csrf

blueprint_labelling = Blueprint('labelling', __name__, template_folder='.')

_per_page = 50


class SearchForm(FlaskForm):
    search = StringField(
        'search (optional)',
        validators=[validators.Optional(), validators.Length(min=2)]
    )

    dialect = SelectField(
        'dialect',
        choices=[('', '-- ?? --'), ('be', 'Bernese'), ('arg', 'Argau')],  # TODO
        validators=[validators.DataRequired()]
    )

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
        if form.save.data:
            saved_count = 0
            for k, v in request.form.items():
                if k.startswith('sentence-'):
                    MongoSentence.objects.with_id(k[9:]).add_label(v)
                    saved_count += 1
            flash_success("Labelled %d sentences." % saved_count)

        elif not form.validate():
            return dict(form=form)

        return redirect(url_for('.add_labels', search=form.search.data, dialect=form.dialect.data))

    elif len(request.args) > 0:
        form.search.data = request.args.get('search', None)
        form.dialect.data = request.args.get('dialect', '')

        if validate_no_csrf(form):
            extra_query = dict(text__icontains=form.search.data) if form.search.data else dict()
            sentences = MongoSentence.objects(
                deleted__exists=False,
                validated_by__exists=True,
                dialects__user__ne=current_user.id,
                **extra_query) \
                .limit(_per_page)

            has_results = True

    return dict(form=form, sentences=sentences, has_results=has_results)
