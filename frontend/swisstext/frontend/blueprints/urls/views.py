from flask import Blueprint
from flask import request, url_for, redirect
from flask_login import login_required, current_user

from swisstext.frontend.persistence.models import MongoURL, MongoSentence, SourceType, Source, MongoBlacklist
from swisstext.frontend.user_management import role_required
from swisstext.frontend.utils.flash import flash_success
from swisstext.frontend.utils.utils import templated
from .forms import DeleteUrlForm, SearchUrlsForm, AddUrlForm

blueprint_urls = Blueprint('urls', __name__, template_folder='templates')


@blueprint_urls.route('/add', methods=['GET', 'POST'])
@login_required
@templated('urls/add.html')
def add():
    form = AddUrlForm()

    if request.method == 'POST':
        if not form.validate():
            return dict(form=form)

        url = form.url.data
        if MongoURL.exists(url):
            return dict(form=form, url_exists=True)

        if form.add1.data:
            base_url = url.split('?')[0]
            if base_url.endswith('/'):
                base_url = base_url[:-1]
            similar_urls = MongoURL.objects(id__icontains=base_url).paginate(page=1, per_page=10)
            if similar_urls.total > 0:
                return dict(form=form, similar_urls=similar_urls)

        MongoURL.create(url, source=Source(type_=SourceType.USER, extra=current_user.id)).save()
        flash_success('The url has been added.')
        return redirect(url_for(request.endpoint))

    return dict(form=form)


@blueprint_urls.route('search', methods=['GET', 'POST'])
@role_required()
@templated('urls/search.html')
def view():
    if request.method == 'GET':
        form = SearchUrlsForm.from_get()
        page = form.get_page_and_reset()  # get the parameter, then reset
        if form.is_blank():
            return dict(form=form, urls=[], collapse=False)
        else:
            query_params = form.get_mongo_params()
            urls = MongoURL.objects(**query_params) \
                .order_by("%s%s" % ('' if form.sort_order.data else '-', form.sort.data)) \
                .paginate(page, per_page=20)
            collapse = urls.total > 0

        return dict(form=form, urls=urls, collapse=collapse)

    else:
        return SearchUrlsForm.redirect_as_get()


@blueprint_urls.route('/<path:id>', methods=['GET', 'POST'])
@login_required
@templated('urls/details.html')
def details(id):
    form = DeleteUrlForm()
    if request.method == 'POST' and form.validate():
        # remove all sentences
        all_sentences = MongoSentence.objects(url=id).fields(id=True)
        MongoSentence.mark_deleted(all_sentences, current_user.id)
        # blacklist url
        MongoURL.try_delete(id)  # remove URL if exists
        MongoBlacklist.add_url(id)

        flash_success("URL '%s' has been blacklisted." % id)
        return redirect(request.args.get('next') or url_for('.view'))

    page = int(request.args.get('page', 1))
    url = MongoURL.objects(id=id).get_or_404()
    sentences = MongoSentence.objects(url=id).order_by('-date_added').paginate(page=page, per_page=20)
    return dict(form=form, url=url, sentences=sentences)
