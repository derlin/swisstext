from flask import Blueprint, request, redirect, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField, SelectMultipleField, widgets, validators, SelectField, \
    BooleanField, StringField

from persistence.models import MongoSentence, Dialects
from user_management import role_required
from utils import flash
from utils.utils import templated

blueprint_sentences = Blueprint('sentences', __name__, template_folder='.')

_per_page = 50

class DeleteSentenceForm(FlaskForm):
    comment = StringField('comment', render_kw=dict(placeholder="optional comment"))
    delete = SubmitField('Go ahead!')

class SentencesForm(FlaskForm):
    # limit = IntegerField(
    #     'Max results',
    #     validators=[validators.Optional(), validators.Length(min=1)]
    # )

    search = StringField(
        'Search',
        validators=[validators.Optional(), validators.Length(min=2)]
    )
    validated_only = BooleanField('Validated sentences only', default=False)
    labelled_only = BooleanField('Labelled sentences only', default=False)

    dialects = SelectMultipleField(
        'Dialects',
        choices=list(Dialects.items()),
        default=[],  # Dialects.items.keys(),
        validators=[validators.Optional()],
        widget=widgets.ListWidget(prefix_label=False),
        option_widget=widgets.CheckboxInput()
    )

    sort = SelectField(
        'Order by',
        choices=[('text', 'A-Z'), ('crawl_proba', 'SG proba'), ('url', 'url'), ('date_added', 'Date added')],
        default='date_added'
    )
    sort_order = BooleanField('Ascending', default=False)
    apply = SubmitField('Apply')
    reset = SubmitField('Reset')

    page = HiddenField(default=1)


@blueprint_sentences.route('', methods=['GET', 'POST'])
@login_required
@templated('sentences.html')
def view():
    form = SentencesForm()
    sentences = []
    page = int(form.page.data)  # get the parameter, then reset
    form.page.data = 1
    collapse = False

    if request.method == 'POST' and form.validate():
        if form.reset.data:
            return redirect(url_for('.view'))

        query_params = dict(deleted__exists=False)

        if len(form.dialects.data):
            if len(form.dialects.data) < len(form.dialects.choices):
                query_params['dialect__label__in'] = form.dialects.data
            else:
                query_params['dialect__label__exists'] = True

        if form.search.data:
            query_params['text__icontains'] = form.search.data.strip()

        if form.validated_only.data:
            query_params['validated_by__0__exists'] = True
        if form.labelled_only.data:
            query_params['dialect.label__exists'] = True

        sentences = MongoSentence.objects(**query_params) \
            .order_by("%s%s" % ('' if form.sort_order.data else '-', form.sort.data)) \
            .paginate(page, per_page=20)

        collapse = sentences.total > 0

    return dict(form=form, sentences=sentences, collapse=collapse)


@blueprint_sentences.route('<sid>', methods=['GET', 'POST'])
@login_required
@templated('details_sentence.html')
def details(sid):
    form = DeleteSentenceForm()
    if request.method == 'POST' and form.validate():
        MongoSentence.mark_deleted(sid, current_user.id, form.comment.data)
        flash.flash_success('Sentence deleted.')
        return redirect(request.referrer or '/')
    return dict(form=form, s=MongoSentence.objects.get_or_404(id=sid))
