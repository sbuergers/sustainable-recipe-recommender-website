""" authentication forms """
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Length, EqualTo,\
    ValidationError, Email
from passlib.hash import pbkdf2_sha512
from application.models import User


def invalid_credentials(form, field):
    """ Username and password checker """

    password = field.data
    username = form.username.data

    # Check username or password is invalid
    user_obj = User.query.filter_by(username=username).first()
    if user_obj is None:
        raise ValidationError("Username or password is incorrect")

    elif not pbkdf2_sha512.verify(password, user_obj.password):
        raise ValidationError("Username or password is incorrect")


class RegistrationForm(FlaskForm):
    username = StringField('username', validators=[
                    InputRequired(message="Username required"),
                    Length(min=4, max=25, message="Username must \
                        be between 4 and 25 characters")
                    ])
    email = StringField('email', validators=[
                    InputRequired(message="Email required"),
                    Email(message="Please enter a valid email address"),
                    Length(min=4, max=35, message="Please \
                        enter a valid email address")
                    ])
    password = PasswordField('password', validators=[
                    InputRequired(message="Password required"),
                    Length(min=8, max=25, message="Password must be \
                        between 8 and 25 characters")
                    ])
    confirm_pswd = PasswordField('confirm_pswd', validators=[
                    InputRequired(message="Password required"),
                    EqualTo('password', message="Passwords \
                        must match")
                    ])
    optin_terms = BooleanField('optin_terms', validators=[
                    InputRequired(message="You have to accept the terms \
                        and conditions to create an account.")])
    optin_news = BooleanField('optin_news')

    def validate_username(self, username):
        user_obj = User.query.filter_by(username=username.data).first()
        if user_obj:
            raise ValidationError("Username already exists. \
                Please select a different username.")

    def validate_email(self, email):
        user_obj = User.query.filter_by(email=email.data).first()
        if user_obj:
            raise ValidationError("There is already an account \
                registered with this email address.")


class LoginForm(FlaskForm):
    username = StringField('username', validators=[
                InputRequired(message="Username required")])
    password = PasswordField('password', validators=[
                InputRequired(message="Password required"),
                invalid_credentials])


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[
                InputRequired(message="Email required"),
                Email(message="Please enter a valid email address")])
    submit = SubmitField('Request Password Reset')


# eof
