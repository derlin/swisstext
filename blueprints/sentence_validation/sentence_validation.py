from flask import Blueprint, request, redirect, url_for
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField

from mongo import MongoSentence
from mongo.urls import MongoURL, MongoBlacklist
from utils.utils import templated
from utils import responses, flash

from urllib.parse import unquote

blueprint_sentence_validation = Blueprint('sentence_validation', __name__, template_folder='.')

_per_page = 50


class ValidationForm(FlaskForm):
    next = HiddenField(default=1)
    sentences_ids = HiddenField()
    submit = SubmitField('validate & next')


class RemoveSiteForm(FlaskForm):
    submit = SubmitField('blacklist URL')


@blueprint_sentence_validation.route('', methods=['GET', 'POST'])
@login_required
@templated('sentence_validation.html')
def validate():
    form = ValidationForm()

    if request.method == 'POST' and form.validate():
        ss = MongoSentence.objects(id__in=form.sentences_ids.data.split(","))
        ss.update(add_to_set__validated_by=current_user.id)
        flash.flash_success('%d sentences validated.' % ss.count())

    sentences = MongoSentence.objects(validated_by__nin=[current_user.id], deleted_by__exists=False) \
        .order_by('crawl_proba') \
        .limit(_per_page)
    form.sentences_ids.data = ",".join((s.id for s in sentences))
    return dict(form=form, sentences=sentences)


@blueprint_sentence_validation.route('/site', methods=['GET', 'POST'])
@login_required
@templated('remove_url.html')
def remove_url():
    form = RemoveSiteForm()
    url = request.args.get('url', "")
    if not url:
        return responses.bad_param("Missing query parameter 'url'")

    sentences = MongoSentence.objects(url=url, deleted_by__exists=False).fields(id=True, text=True, crawl_proba=True)

    if request.method == 'POST' and form.validate():
        sentences.update(deleted_by=current_user.id)
        # TODO blacklist url as well
        murl = MongoURL.objects.with_id(url)
        MongoBlacklist(url=url, date_added=murl.delta_date).save()
        murl.delete()
        flash.flash_success("URL '%s' has been blacklisted." % unquote(url))
        return redirect(url_for('.validate'))

    return dict(url=url, form=form, sentences=sentences)


def old():
    page = int(request.args.get('page', 1))
    # queryset = MongoSentence.objects(__raw__={"validation": {"$ne": [current_user.id]}})
    queryset = MongoSentence.objects(validation__nin=[current_user.id], deleted_by__ne=None)
    sentences = queryset \
        .order_by('-crawl_proba') \
        .paginate(page=page, per_page=10)

    return dict(sentences=sentences)
