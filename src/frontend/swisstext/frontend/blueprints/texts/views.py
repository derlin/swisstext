from types import SimpleNamespace

from flask import Blueprint, request
from flask_login import login_required
from swisstext.frontend.utils.utils import templated
from swisstext.frontend.persistence.models import MongoText, MongoURL

from .forms import SearchTextsForm

blueprint_texts = Blueprint('texts', __name__, template_folder='templates')


@blueprint_texts.route('/search', methods=['GET', 'POST'])
@login_required
@templated('texts/search.html')
def view():
    if request.method == 'POST':
        return SearchTextsForm.redirect_as_get()

    form = SearchTextsForm.from_get()
    page = form.get_page_and_reset()  # get the parameter, then reset
    if form.is_blank():
        return dict(form=form, urls=[], collapse=False)
    else:
        query_params = form.get_mongo_params()
        texts = MongoText.objects(**query_params) \
            .order_by("%s%s" % ('' if form.sort_order.data else '-', form.sort.data)) \
            .paginate(page, per_page=20)
        collapse = texts.total > 0

        return dict(form=form, texts=texts, collapse=collapse)


@blueprint_texts.route('/<id>', methods=['GET', 'POST'])
@login_required
@templated('texts/details.html')
def details(id):
    mt = MongoText.objects(id=id).get_or_404()
    # use simplenamespace to simulate a pagination result, so we can reuse
    # the urls/_table.html template to show urls
    urls = SimpleNamespace(items=MongoURL.objects(id__in=mt.urls))
    return dict(mongo_text=mt, urls=urls)
