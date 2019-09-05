from flask import Blueprint, request, redirect, url_for
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from markupsafe import Markup
from wtforms import HiddenField, SubmitField

from swisstext.frontend.persistence.models import MongoSentence, MongoURL
from swisstext.frontend.utils import flash
from swisstext.frontend.utils.utils import templated

blueprint_validation = Blueprint('validation', __name__, template_folder='templates')

_per_page = 100  # TODO: back to 50 after renato finishes


class ValidationForm(FlaskForm):
    next = HiddenField(default=1)
    sentences_ids = HiddenField()
    submit = SubmitField('validate & next')


@blueprint_validation.route('', methods=['GET', 'POST'])
@login_required
@templated('validation/index.html')
def validate():
    form = ValidationForm()
    param_uid = request.args.get('uid', None)
    url = None # set if the uid parameter is present AND valid

    if request.method == 'POST' and form.validate():
        ss = MongoSentence.objects(id__in=form.sentences_ids.data.split(","))
        ss.update(add_to_set__validated_by=current_user.id)
        flash.flash_success('%d sentences validated.' % ss.count())
        return redirect(url_for(request.endpoint, **request.args))  # avoid form resubmission on refresh

    mongo_params = dict(validated_by__nin=[current_user.id], deleted__exists=False)

    if param_uid is not None:
        # add a filter to the Mongo Query (only if the uid is valid)
        mu = MongoURL.get(id=param_uid)
        if mu is None:
            flash.flash_error(Markup(f'url <code>{mu.id}</code> does not exist.'))
        else:
            url = mu.url
            mongo_params['url'] = url

    sentences = MongoSentence.objects(**mongo_params) \
        .order_by('url', 'date_added') \
        .limit(_per_page)

    if not sentences and param_uid:
        # we were displaying urls from a given URL, but they are all
        # validated now... Redirect to the main view
        flash.flash_warning(Markup(f'No more sentences to validate from URL <code>{param_uid}</code>.'))
        return redirect(url_for(request.endpoint))

    form.sentences_ids.data = ",".join((s.id for s in sentences))
    return dict(form=form, sentences=sentences, url=url)
