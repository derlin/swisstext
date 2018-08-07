from flask import Blueprint, redirect, request, url_for
from flask_login import current_user, login_user, login_required
from markupsafe import Markup

from swisstext.frontend.persistence.models import MongoSentence
from swisstext.frontend.user_management import User
from swisstext.frontend.utils.flash import flash_form_errors, flash_error, flash_success
from swisstext.frontend.utils.utils import templated

from .forms import LoginForm, ProfileForm

blueprint_users = Blueprint('users', __name__, template_folder='templates')


@blueprint_users.route('/login', methods=['GET', 'POST'])
@templated('users/login.html')
def login():
    if current_user.is_authenticated == True:
        return redirect('/')

    form = LoginForm()
    if request.method == 'POST':
        if not form.validate():
            flash_form_errors(form)
            return dict(form=form)
        else:
            user = User.get(form.name.data, form.password.data)
            if user:
                login_user(user)
                return redirect('/')
            else:
                flash_error('Invalid login information.')

    return dict(form=form)


@blueprint_users.route('/profile', methods=['GET', 'POST'])
@templated('users/profile.html')
@login_required
def profile():
    page = int(request.args.get('page', 1))
    form = ProfileForm()

    if request.method == 'POST' and form.validate():
        # here, if you don't hold a reference to s, you will randomly get a
        # ReferenceError: weakly-reference no longer exists...
        s = MongoSentence.objects.with_id(form.sid.data)
        s.dialect.remove_label(current_user.id)
        flash_success(
            Markup(
                'Label removed from sentence <a href="%s"><code>%s</code></a>.') % (
                url_for('sentences.details', sid=s.id), s.id))
        return redirect(url_for(request.endpoint))

    skipped_count = MongoSentence.objects(dialect__skipped_by=current_user.id).count()
    vcount = MongoSentence.objects(validated_by=current_user.id).count()

    ss = MongoSentence.objects(dialect__labels__user=current_user.id) \
        .fields(**{'dialect.labels.$': True, 'text': True}) \
        .order_by('-dialect.labels.date') \
        .paginate(page, per_page=10)
    return dict(form=form, valid_count=vcount, skipped_count=skipped_count, labelled_sentences=ss)
