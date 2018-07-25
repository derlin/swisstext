from flask import Blueprint, redirect, request, url_for
from flask_login import current_user, login_user, login_required
from flask_wtf import FlaskForm
from markupsafe import Markup
from wtforms import PasswordField, StringField, SubmitField, HiddenField
from wtforms.validators import Length, InputRequired

from persistence.models import MongoSentence
from utils.flash import flash_form_errors, flash_error, flash_success
from utils.utils import templated
from user_management import User

blueprint_users = Blueprint('users', __name__, template_folder='.')


class LoginForm(FlaskForm):
    name = StringField(
        'name',
        validators=[InputRequired(), Length(max=30)])

    password = PasswordField(
        'password',
        validators=[InputRequired(), Length(min=8, max=20)])

    submit = SubmitField('submit')


class RegisterForm(LoginForm):
    password_bis = PasswordField(
        'repeat password',
        validators=[InputRequired(), Length(min=8, max=20)])


@blueprint_users.route('/login', methods=['GET', 'POST'])
@templated('login.html')
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


class ProfileForm(FlaskForm):
    sid = HiddenField()


@blueprint_users.route('/profile', methods=['GET', 'POST'])
@templated('profile.html')
@login_required
def profile():
    page = int(request.args.get('page', 1))
    form = ProfileForm()

    if request.method == 'POST' and form.validate():
        sid = form.sid.data
        MongoSentence.remove_label(sid, current_user.id)
        flash_success(
            Markup(
                'Label removed from sentence <a href="%s"><code>%s</code></a>.') % (
            url_for('sentences.details', sid=sid), sid))
        return redirect(url_for(request.endpoint))

    vcount = MongoSentence.objects(dialect__skipped_by=current_user.id).count()
    ss = MongoSentence.objects(dialect__labels__user=current_user.id) \
        .fields(**{'dialect.labels.$': True, 'text': True}) \
        .order_by('-dialect.labels.date') \
        .paginate(page, 5)
    return dict(form=form, valid_count=vcount, labelled_sentences=ss)
