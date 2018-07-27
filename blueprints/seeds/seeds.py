from flask import Blueprint, request, url_for, redirect
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, validators, SelectField, HiddenField, IntegerField

from persistence.models import MongoSeed, SourceType, Source, MongoURL
from utils.flash import flash_success
from utils.search_form import SearchForm
from utils.utils import templated

blueprint_seeds = Blueprint('seeds', __name__, template_folder='.')


class AddSeedForm(FlaskForm):
    seed = StringField(
        render_kw=dict(placeholder='Swiss German search term(s)'),
        validators=[validators.Length(min=3), validators.DataRequired()]
    )
    test = SubmitField('Submit')
    cancel = SubmitField('Cancel')
    add = SubmitField('I am sure, add it!')


class SearchSeedsForm(SearchForm):
    search = StringField(
        'Search',
        validators=[validators.Optional(), validators.Length(min=2)]
    )
    min_count = IntegerField(
        'Min URLs',
        validators=[validators.Optional()],
        default=0
    )

    search_history = SelectField(
        'Crawls',
        choices=[('', 'any'), ('False', 'Never crawled'), ('True', 'Crawled at least once')],
        validators=[validators.Optional()]
    )
    sort = SelectField(
        'Order by',
        choices=[('id', 'A-Z'), ('count', 'Num URLs'), ('date_added', 'Creation date')],
        default='delta_date'
    )

    sort_order = BooleanField('Ascending', default=True)
    apply = SubmitField('Apply')
    reset = SubmitField('Reset')

    page = HiddenField(default=1)


@blueprint_seeds.route('add', methods=['GET', 'POST'])
@login_required
@templated('add_seed.html')
def add():
    form = AddSeedForm()
    similar_seeds = None
    add_mode = False

    if request.method == 'POST' and form.validate():
        seed = form.seed.data

        if form.test.data:
            if MongoSeed.exists(seed):
                form.seed.errors = ('', 'This seed already exists.')
            else:
                similar_seeds = MongoSeed.find_similar(seed)
                add_mode = True

        elif form.add.data:
            MongoSeed.create(seed, Source(SourceType.USER, current_user.id)).save()
            flash_success("Seed '%s' added !" % seed)
            return redirect(url_for('.add'))

        else:  # cancel was pressed
            return redirect(url_for('.add'))

    return dict(form=form, add_mode=add_mode, similar_seeds=similar_seeds)


@blueprint_seeds.route('/view', methods=['GET', 'POST'])
@login_required
@templated('view_seeds.html')
def view():
    if request.method == 'POST':
        return SearchSeedsForm.redirect_as_get()

    form: SearchSeedsForm = SearchSeedsForm.from_get()
    page = int(form.page.data)  # get the parameter, then reset
    form.page.data = 1
    query_params = dict()

    if not form.is_blank():

        if form.reset.data:
            return redirect(url_for('.view'))

        if form.search.data:
            query_params['id__icontains'] = form.search.data.strip()

        if form.min_count.data and form.min_count.data > 0:
            query_params['count__gte'] = form.min_count.data

        if form.search_history.data:
            query_params['search_history__0__exists'] = form.search_history.data == 'True'

    seeds = MongoSeed.objects(**query_params) \
        .order_by("%s%s" % ('' if form.sort_order.data else '-', form.sort.data)) \
        .paginate(page, per_page=20)

    return dict(form=form, seeds=seeds)


@blueprint_seeds.route('/details/<id>', methods=['GET'])
@login_required
@templated('details_seed.html')
def details(id):
    page = int(request.args.get('page', 1))
    seed = MongoSeed.objects(id=id).get_or_404()
    urls = MongoURL.objects(source__extra=id).order_by('-date_added').paginate(page=page, per_page=10)
    return dict(s=seed, urls=urls)
