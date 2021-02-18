""" authentication flask routes """

# Flask modules and forms
from flask import render_template, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user
from flask_login import login_required

# Security
from passlib.hash import pbkdf2_sha512

# User made modules
from application.auth.forms import RegistrationForm, LoginForm, \
    ResetPasswordRequestForm, ResetPasswordForm

# Database
from application import db
from application.models import User, Consent
from application.auth import bp
import datetime

# Email
from application.auth.email import send_password_reset_email


@bp.route('/signup', methods=['GET', 'POST'])
def signup():

    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    reg_form = RegistrationForm()

    if reg_form.validate_on_submit():
        username = reg_form.username.data
        password = reg_form.password.data
        email = reg_form.email.data
        optin_news = reg_form.optin_news.data

        # Add user to DB
        user = User(username=username,
                    password=pbkdf2_sha512.hash(password),
                    email=email,
                    confirmed=False,
                    created_on=datetime.datetime.utcnow(),
                    optin_news=optin_news)
        db.session.add(user)
        db.session.commit()

        # Add consent to DB (if given)
        if optin_news:
            consent = Consent(userID=user.userID,
                              consent_type='news',
                              consent_given_on=datetime.datetime.utcnow(),
                              consent_given_via='signup_form')
            db.session.add(consent)
            db.session.commit()

            # email verification needed for newsletter
            # TODO flash msg + send verification email

        flash('Account registered successfully. Please login.', 'success')
        return redirect(url_for('auth.signin'))

    return render_template('signup.html', reg_form=reg_form)


@bp.route("/signin", methods=['GET', 'POST'])
def signin():

    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    login_form = LoginForm()

    if login_form.validate_on_submit():
        user_obj = User.query.filter_by(
                       username=login_form.username.data).first()
        login_user(user_obj, remember=False)
        return redirect(url_for('main.home'))

    return render_template('signin.html', login_form=login_form)


@bp.route("/logout", methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@bp.route("/terms_and_conditions")
def terms_and_conditions():
    return render_template('terms-and-conditions.html')


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('auth.signin'))
    return render_template('reset-password-request.html',
                           title='Reset Password', form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.home'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = pbkdf2_sha512.hash(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('auth.signin'))
    return render_template('reset-password.html', form=form)


# eof
