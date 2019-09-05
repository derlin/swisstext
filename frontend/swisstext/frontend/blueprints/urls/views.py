from flask import Blueprint
from flask import request, url_for, redirect
from flask_login import login_required, current_user
from markupsafe import Markup

from swisstext.frontend.persistence.models import MongoURL, MongoSentence, SourceType, Source, MongoBlacklist
from swisstext.frontend.user_management import role_required
from swisstext.frontend.utils.flash import flash_success, flash_error
from swisstext.frontend.utils.utils import templated
from .forms import DeleteUrlForm, SearchUrlsForm, AddUrlForm, DeleteUrlsForm

blueprint_urls = Blueprint('urls', __name__, template_folder='templates')


@blueprint_urls.route('/add', methods=['GET', 'POST'])
@login_required
@templated('urls/add.html')
def add():
    form = AddUrlForm()

    if request.method == 'POST':
        # submitted either with add1 (first submission) or add2 (there was similar matches, ask for confirmation)
        if not form.validate():
            return dict(form=form)

        url = form.url.data
        if MongoURL.exists(url):
            return dict(form=form, url_exists=True)

        if form.add1.data:
            # first submission: check for similar matches
            # TODO use urllib.urlparse
            base_url = url.split('?')[0]
            if base_url.endswith('/'):
                base_url = base_url[:-1]
            similar_urls = MongoURL.objects(url__icontains=base_url).paginate(page=1, per_page=10)
            if similar_urls.total > 0:
                return dict(form=form, similar_urls=similar_urls)

        mu = MongoURL.create(url, source=Source(type_=SourceType.USER, extra=current_user.id))#.save()
        flash_success(Markup(f'The url has been added: <a href=""><code>{mu.id}</code></a>'))
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

        return dict(form=form, delete_form=DeleteUrlsForm(), urls=urls, collapse=collapse)

    else:
        delete_form = DeleteUrlsForm()

        if delete_form.go.data:
            # the delete form is only available after search,
            # so the url should contain some query parameters

            if not delete_form.validate():
                # ensure the checkbox is selected to avoid silly mistakes
                flash_error('You must know what you are doing.')
                return redirect(request.url)

            form = SearchUrlsForm.from_get()
            if not form.search.data:
                # don't let the user delete everything
                flash_error('You must have some filtering before delete.')
                return redirect(request.url)

            urls = MongoURL.objects(**form.get_mongo_params())
            ud, sd = 0, 0
            for url in urls:
                try:
                    sd += _delete_url(url.id)
                    ud += 1
                except Exception as e:
                    print(e)

            flash_success(f'Delete {ud}/{len(urls)} urls ({sd} sentences).')
            return redirect(request.url)

        return SearchUrlsForm.redirect_as_get()


@blueprint_urls.route('/<id>', methods=['GET', 'POST'])
@login_required
@templated('urls/details.html')
def details(id):
    form = DeleteUrlForm()
    mu = MongoURL.objects(id=id).get_or_404()

    if request.method == 'POST' and form.validate():
        num_sentences = _delete_url(mu)
        msg = f'URL <small>{mu.url}</small> (id: <code>{mu.id}</code>) has been blacklisted.'
        if num_sentences > 0:
            msg += f'<br>{num_sentences} sentence(s) deleted.'
        flash_success(Markup(msg))
        return redirect(request.args.get('next') or url_for('.view'))

    page = int(request.args.get('page', 1))

    sentences = MongoSentence.objects(url=mu.url).order_by('-date_added').paginate(page=page, per_page=20)
    return dict(form=form, url=mu, sentences=sentences)


def _delete_url(mu: MongoURL):
    # remove all sentences
    all_sentences = MongoSentence.objects(url=mu.url).fields(id=True)
    MongoSentence.mark_deleted(all_sentences, current_user.id)
    # blacklist url
    MongoURL.try_delete(mu.id)  # remove URL if exists
    MongoBlacklist.add_url(mu.url)

    return len(all_sentences)
