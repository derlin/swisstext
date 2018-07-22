from flask import Blueprint, redirect, url_for
from flask import request
from flask_login import login_required, current_user

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, RadioField, HiddenField
from wtforms import validators

from persistence.models import MongoSentence
from utils.flash import flash_success, flash_info, flash_form_errors, flash_warning
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
        choices=[('be', 'Bernese'), ('arg', 'Argau'), ('', '-- ?? --')],  # TODO
        validators=[validators.DataRequired()]
    )

    submit = SubmitField('Search')
    save = SubmitField('Save and next')


@blueprint_labelling.route('/old', methods=['GET', 'POST'])
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
                dialect__labels__user__ne=current_user.id,
                **extra_query) \
                .limit(_per_page)

            has_results = True

    return dict(form=form, sentences=sentences, has_results=has_results)


# -----------------------------

class RadioForm(FlaskForm):
    dialect = RadioField(
        'dialect',
        choices=[('?', 'No idea'), ('be', 'Bernese'), ('arg', 'Argau')],  # TODO
        default='?',
        validators=[validators.DataRequired()]
    )

    sentence_id = HiddenField()
    delete_sentence = SubmitField('x', render_kw=dict(title="Delete sentence completely."))


@blueprint_labelling.route('', methods=['GET', 'POST'])
@login_required
@templated('labelling-radios.html')
def add_labels_radio():
    form = RadioForm()

    if request.method == 'POST':
        s = MongoSentence.objects.with_id(form.sentence_id.data)
        if s and form.validate():
            if form.delete_sentence.data:
                MongoSentence.mark_deleted(s, current_user.id)
                flash_warning('Sentence deleted.')
            elif form.dialect.data != '?':
                MongoSentence.add_label(s, label=form.dialect.data, uuid=current_user.id)
                flash_success("Sentence labelled.")
            else:
                s.update(add_to_set__dialect__skipped_by=current_user.id)
                flash_info("Sentence skipped.")
        else:
            flash_form_errors(form)
        return redirect(url_for('.add_labels_radio'))

    sentence = MongoSentence.objects(
        deleted__exists=False,
        validated_by__exists=True,
        dialect__skipped_by__ne=current_user.id,
        dialect__labels__user__ne=current_user.id) \
        .fields(id=1, url=1, text=1) \
        .first()

    form.sentence_id.data = sentence.id
    return dict(form=form, sentence=sentence)
