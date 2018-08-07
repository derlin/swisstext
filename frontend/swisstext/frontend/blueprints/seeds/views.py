from flask import Blueprint, request, url_for, redirect
from flask_login import login_required, current_user

from swisstext.frontend.persistence.aggregation_utils import paginated_aggregation
from swisstext.frontend.persistence.models import MongoSeed, SourceType, Source, MongoURL
from swisstext.frontend.user_management import role_required
from swisstext.frontend.utils.flash import flash_success
from swisstext.frontend.utils.utils import templated

from .forms import AddSeedForm, SearchSeedsForm, DeleteSeedForm

blueprint_seeds = Blueprint('seeds', __name__, template_folder='templates')


@blueprint_seeds.route('add', methods=['GET', 'POST'])
@login_required
@templated('seeds/add.html')
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
@role_required()
@templated('seeds/search.html')
def view():
    if request.method == 'GET':
        form: SearchSeedsForm = SearchSeedsForm.from_get()
        page = form.get_page_and_reset()  # get the parameter, then reset
        if form.is_blank():
            form = SearchSeedsForm()
        #     return dict(form=form, seeds=[], collapse=False)
        # else:
        pipeline = form.get_search_pipeline()
        seeds = paginated_aggregation(MongoSeed, pipeline, page=page, per_page=20)
        return dict(form=form, seeds=seeds, collapse=seeds.total > 0)
    else:
        return SearchSeedsForm.redirect_as_get()


@blueprint_seeds.route('/details/<id>', methods=['GET', 'POST'])
@login_required
@templated('seeds/details.html')
def details(id):
    form = DeleteSeedForm()

    if request.method == 'POST' and form.validate():
        seed = MongoSeed.objects.with_id(id)
        if seed.search_history:
            seed.mark_deleted(seed, current_user.id, form.comment.data)
        else:
            seed.delete()
            return redirect(url_for('.view'))
        return redirect(url_for(request.endpoint, id=id))

    seed = MongoSeed.objects(id=id).get_or_404()
    # TODO : show pertinence information here as well ?
    # from .forms import get_default_seeds_pipeline
    # pipeline = get_default_seeds_pipeline()
    # pipeline.append({'$match': {'_id': id}})
    # seed_2 = MongoSeed.objects.aggregate(*pipeline).next()
    page = int(request.args.get('page', 1))
    urls = MongoURL.objects(source__extra=id).order_by('-date_added').paginate(page=page, per_page=10)
    return dict(form=form, s=seed, urls=urls)
