from flask import Blueprint, redirect, url_for, request
from flask_login import current_user, login_user
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import Length, InputRequired

from mongo import User
from utils.flash import flash_form_errors, flash_error
from utils.utils import templated

blueprint_users = Blueprint('users', __name__)


class LoginForm(FlaskForm):
    name = StringField(
        'name',
        validators=[InputRequired(), Length(max=30)])

    password = PasswordField(
        'password',
        validators=[InputRequired(), Length(min=8, max=20)])


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
            user = User.from_name(form.name.data, form.password.data)
            if user:
                login_user(user)
                return redirect('/')
            else:
                flash_error('Invalid login information.')

    return dict(form=form)
