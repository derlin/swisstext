from flask import Blueprint, request, redirect, Response
from flask_login import current_user, login_required

from swisstext.frontend.persistence.models import MongoSentence
from swisstext.frontend.user_management import role_required
from swisstext.frontend.utils import flash
from swisstext.frontend.utils.utils import templated

from .forms import DeleteSentenceForm, SentencesForm
from .export import stream_csv

blueprint_sentences = Blueprint('sentences', __name__, template_folder='templates')
_per_page = 50


@blueprint_sentences.route('', methods=['GET', 'POST'])
@role_required()
@templated('sentences/search.html')
def view():
    if request.method == 'GET':
        form = SentencesForm.from_get()
        if SentencesForm.is_blank():
            # don't show any results the first time
            # TODO really necessary ?
            return dict(form=form, sentences=[], collapse=False)
        else:
            page = form.get_page_and_reset()
            query_params = form.get_mongo_params(deleted__exists=False)
            sentences = MongoSentence.objects(**query_params) \
                .order_by("%s%s" % ('' if form.sort_order.data else '-', form.sort.data)) \
                .paginate(page, per_page=20)
            collapse = sentences.total > 0

            return dict(form=form, sentences=sentences, collapse=collapse)
    else:
        return SentencesForm.redirect_as_get()

@blueprint_sentences.route('/export')
def export_csv():
    form = SentencesForm.from_get()
    sentences = MongoSentence.objects(**form.get_mongo_params(deleted__exists=False))
    return Response(stream_csv(sentences), mimetype='text/csv')

@blueprint_sentences.route('<sid>', methods=['GET', 'POST'])
@login_required
@templated('sentences/details.html')
def details(sid):
    form = DeleteSentenceForm()
    if request.method == 'POST' and form.validate():
        MongoSentence.mark_deleted(sid, current_user.id, form.comment.data)
        flash.flash_success('Sentence deleted.')
        return redirect(request.referrer or '/')
    return dict(form=form, s=MongoSentence.objects.get_or_404(id=sid))
