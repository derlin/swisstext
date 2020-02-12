from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, HiddenField
from wtforms import validators


class LoginForm(FlaskForm):
    name = StringField(
        'name',
        validators=[validators.InputRequired(), validators.Length(max=30)])

    password = PasswordField(
        'password',
        validators=[validators.InputRequired(), validators.Length(min=8, max=20)])

    submit = SubmitField('submit')


class RegisterForm(LoginForm):
    password_bis = PasswordField(
        'repeat password',
        validators=[validators.InputRequired(), validators.Length(min=8, max=20)])


class ProfileForm(FlaskForm):
    sid = HiddenField()
