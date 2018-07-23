from urllib.parse import unquote

from flask import Blueprint, request, redirect, url_for
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField

from persistence.models import MongoSentence, MongoURL, MongoBlacklist
from utils import responses, flash
from utils.utils import templated

blueprint_validation = Blueprint('validation', __name__, template_folder='.')

_per_page = 50


class ValidationForm(FlaskForm):
    next = HiddenField(default=1)
    sentences_ids = HiddenField()
    submit = SubmitField('validate & next')


class RemoveSiteForm(FlaskForm):
    cancel = SubmitField('cancel')
    submit = SubmitField('remove sentences & blacklist URL')


@blueprint_validation.route('', methods=['GET', 'POST'])
@login_required
@templated('validation.html')
def validate():
    form = ValidationForm()

    if request.method == 'POST' and form.validate():
        ss = MongoSentence.objects(id__in=form.sentences_ids.data.split(","))
        ss.update(add_to_set__validated_by=current_user.id)
        flash.flash_success('%d sentences validated.' % ss.count())
        return redirect(url_for('.validate'))  # avoid form resubmission on refresh

    sentences = MongoSentence.objects(validated_by__nin=[current_user.id], deleted__exists=False) \
        .order_by('crawl_proba') \
        .limit(_per_page)
    form.sentences_ids.data = ",".join((s.id for s in sentences))
    return dict(form=form, sentences=sentences)


@blueprint_validation.route('/site', methods=['GET', 'POST'])
@login_required
@templated('remove_url.html')
def remove_url():
    form = RemoveSiteForm()
    url = request.args.get('url', "")
    if not url:
        return responses.bad_param("Missing query parameter 'url'")


    if request.method == 'POST' and form.validate():
        if form.submit.data:
            # remove all sentences
            all_sentences = MongoSentence.objects(url=url).fields(id=True)
            MongoSentence.mark_deleted(all_sentences, current_user.id)
            # blacklist url
            MongoURL.try_delete(url)  # remove URL if exists
            MongoBlacklist.add_url(url)

            flash.flash_success("URL '%s' has been blacklisted." % unquote(url))
            return redirect(url_for('.validate'))

        elif form.cancel.data:
            return redirect(url_for('.validate'))

    page = int(request.args.get('page', 1))
    sentences = MongoSentence.objects(url=url, deleted__exists=False)\
        .fields(id=True, text=True, crawl_proba=True).paginate(page=page, per_page=20)

    return dict(url=url, form=form, sentences=sentences)


def old():
    page = int(request.args.get('page', 1))
    # queryset = MongoSentence.objects(__raw__={"validation": {"$ne": [current_user.id]}})
    queryset = MongoSentence.objects(validation__nin=[current_user.id], deleted_by__ne=None)
    sentences = queryset \
        .order_by('-crawl_proba') \
        .paginate(page=page, per_page=10)

    return dict(sentences=sentences)
