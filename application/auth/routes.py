""" authentication flask routes """

# Flask modules and forms
from flask import render_template, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user
from flask_login import login_required

# Security
from passlib.hash import pbkdf2_sha512

# User made modules
from application.auth.forms import RegistrationForm, LoginForm

# Database
from application import db
from application.models import User
from application.auth import bp
import datetime


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

        # Add username & hashed password to DB
        user = User(username=username,
                    password=pbkdf2_sha512.hash(password),
                    email=email,
                    confirmed=False,
                    created_on=datetime.datetime.utcnow(),
                    optin_news=optin_news)
        db.session.add(user)
        db.session.commit()

        flash('Registered successfully. Please login.', 'success')
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
        flash('You have logged in successfully.', 'success')
        return redirect(url_for('main.home'))

    return render_template('signin.html', login_form=login_form)


@bp.route("/logout", methods=['GET'])
@login_required
def logout():
    if current_user.is_anonymous:
        return redirect(url_for('main.home'))

    logout_user()
    flash('You have logged out successfully.', 'success')
    return redirect(url_for('main.home'))


@bp.route("/terms_and_conditions")
def terms_and_conditions():
    return render_template('terms_and_conditions.html')


# eof
