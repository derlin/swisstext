from flask import Blueprint, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField

from mongo import MongoSentence
from utils.utils import templated

blueprint_sentence_validation = Blueprint('sentence_validation', __name__, template_folder='.')

_per_page = 50


class ValidationForm(FlaskForm):
    next = HiddenField(default=1)
    sentences_ids = HiddenField()
    submit = SubmitField('validate & next')


@blueprint_sentence_validation.route('', methods=['GET', 'POST'])
@login_required
@templated('sentence_validation.html')
def index():
    form = ValidationForm()

    if request.method == 'POST' and form.validate():
        ss = MongoSentence.objects(id__in=form.sentences_ids.data.split(","))
        ss.update(add_to_set__validation=current_user.id)

    sentences = MongoSentence.objects(validation__nin=[current_user.id], deleted_by__exists=False) \
        .order_by('crawl_proba') \
        .limit(_per_page)
    form.sentences_ids.data = ",".join((s.id for s in sentences))
    return dict(form=form, sentences=sentences)


def old():
    page = int(request.args.get('page', 1))
    # queryset = MongoSentence.objects(__raw__={"validation": {"$ne": [current_user.id]}})
    queryset = MongoSentence.objects(validation__nin=[current_user.id], deleted_by__ne=None)
    sentences = queryset \
        .order_by('-crawl_proba') \
        .paginate(page=page, per_page=10)

    return dict(sentences=sentences)
