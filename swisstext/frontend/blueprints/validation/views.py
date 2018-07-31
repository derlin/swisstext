from flask import Blueprint, request, redirect, url_for
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField

from swisstext.frontend.persistence.models import MongoSentence
from swisstext.frontend.utils import flash
from swisstext.frontend.utils.utils import templated

blueprint_validation = Blueprint('validation', __name__, template_folder='templates')

_per_page = 50


class ValidationForm(FlaskForm):
    next = HiddenField(default=1)
    sentences_ids = HiddenField()
    submit = SubmitField('validate & next')

@blueprint_validation.route('', methods=['GET', 'POST'])
@login_required
@templated('validation/index.html')
def validate():
    form = ValidationForm()

    if request.method == 'POST' and form.validate():
        ss = MongoSentence.objects(id__in=form.sentences_ids.data.split(","))
        ss.update(add_to_set__validated_by=current_user.id)
        flash.flash_success('%d sentences validated.' % ss.count())
        return redirect(url_for('.validate'))  # avoid form resubmission on refresh

    sentences = MongoSentence.objects(validated_by__nin=[current_user.id], deleted__exists=False) \
        .order_by('-crawl_proba') \
        .limit(_per_page)
    form.sentences_ids.data = ",".join((s.id for s in sentences))
    return dict(form=form, sentences=sentences)