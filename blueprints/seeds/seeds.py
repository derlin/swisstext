from flask import Blueprint, request, url_for, redirect
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Length, DataRequired

from persistence.models import MongoSeed, SourceType, Source
from utils.flash import flash_success
from utils.utils import templated

blueprint_seeds = Blueprint('seeds', __name__, template_folder='.')


class AddSeedForm(FlaskForm):
    seed = StringField(
        render_kw=dict(placeholder='Swiss German search term(s)'),
        validators=[Length(min=3), DataRequired()]
    )
    test = SubmitField('Submit')
    cancel = SubmitField('Cancel')
    add = SubmitField('I am sure, add it!')


@blueprint_seeds.route('', methods=['GET', 'POST'])
@login_required
@templated('add_seed.html')
def add_seed():
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
            return redirect(url_for('.add_seed'))

        else: # cancel was pressed
            return redirect(url_for('.add_seed'))

    return dict(form=form, add_mode=add_mode, similar_seeds=similar_seeds)
