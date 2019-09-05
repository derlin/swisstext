from types import SimpleNamespace

from flask import Blueprint
from flask_login import login_required
from swisstext.frontend.utils.utils import templated
from swisstext.frontend.persistence.models import MongoText, MongoURL

blueprint_texts = Blueprint('texts', __name__, template_folder='templates')


@blueprint_texts.route('/<id>', methods=['GET', 'POST'])
@login_required
@templated('texts/details.html')
def details(id):
    mt = MongoText.objects(id=id).get_or_404()
    # use simplenamespace to simulate a pagination result, so we can reuse
    # the urls/_table.html template to show urls
    urls = SimpleNamespace(items=MongoURL.objects(id__in=mt.urls))
    return dict(mongo_text=mt, urls=urls)
