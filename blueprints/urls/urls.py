from flask import Blueprint, request, url_for, redirect
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, SelectField, IntegerField, HiddenField
from wtforms.validators import Length, Optional

from persistence.models import MongoURL, MongoSentence, MongoBlacklist
from utils.flash import flash_success
from utils.search_form import SearchForm
from utils.utils import templated

blueprint_urls = Blueprint('urls', __name__, template_folder='.')


class SearchUrlsForm(SearchForm):
    search = StringField(
        render_kw=dict(placeholder='url part'),
        validators=[Length(min=2), Optional()]
    )
    min_count = IntegerField(
        'Min sentences',
        validators=[Optional()],
        default=0
    )
    crawl_history = SelectField(
        'Crawls',
        choices=[('', 'any'), ('False', 'Never crawled'), ('True', 'Crawled at least once')],
        validators=[Optional()]
    )

    sort = SelectField(
        'Order by',
        choices=[('url', 'A-Z'), ('delta_date', 'Last crawl date'), ('count', 'Sentences count')],
        default='delta_date'
    )
    sort_order = BooleanField('Ascending', default=False)
    apply = SubmitField('Apply')
    reset = SubmitField('Reset')

    page = HiddenField(default=1)


class DeleteUrlForm(FlaskForm):
    delete = SubmitField('Remove sentences & blacklist URL')


@blueprint_urls.route('search', methods=['GET', 'POST'])
@login_required
@templated('urls.html')
def view():
    if request.method == 'POST':
        return SearchUrlsForm.redirect_as_get()

    form = SearchUrlsForm.from_get()
    urls = []
    page = int(form.page.data)  # get the parameter, then reset
    form.page.data = 1
    collapse = False

    if not form.is_blank():
        query_params = dict()

        if form.search.data:
            query_params['id__icontains'] = form.search.data.strip()

        if form.min_count.data and form.min_count.data > 0:
            query_params['count__gte'] = form.min_count.data

        if form.crawl_history.data:
            query_params['crawl_history__0__exists'] = form.crawl_history.data == 'True'

        urls = MongoURL.objects(**query_params) \
            .order_by("%s%s" % ('' if form.sort_order.data else '-', form.sort.data)) \
            .paginate(page, per_page=20)

        collapse = urls.total > 0

    return dict(form=form, urls=urls, collapse=collapse)


@blueprint_urls.route('/<path:id>', methods=['GET', 'POST'])
@login_required
@templated('details_url.html')
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
