# inspired by
# https://rapidapi.com/blog/build-food-website/
# https://github.com/sandeepsudhakaran/rchat-app
# https://www.youtherokuube.com/watch?v=w25ea_I89iM&t=286s

# Get environment variables (API key)
import os

# Import flask tools
from flask import Flask, render_template, request, redirect, url_for, flash
from flask import session
from flask_login import LoginManager, login_user, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy

# Data handling
import pandas as pd
import numpy as np

# hash function for encrypting passwords
from passlib.hash import pbkdf2_sha512

# form and database modules (self-written)
from wtform_fields import RegistrationForm, LoginForm
from wtform_fields import invalid_credentials, SearchForm
from sql_tables import User

# functions for connecting to AWS RDS postgres DB
from sql_queries import postgresConnect, exact_recipe_match

# functions for recommending and parsing recipe data
from recommend import content_based_search
import helper_functions as hf

# figure functions
import altair_plots as ap


# debug mode (set to True for development, False for deployment)
debug = False


# Configure app
app = Flask(__name__)
#csrf = CsrfProtect(app) # cross site request forgery protection
app.secret_key = os.environ.get('SECRET')
app.config['WTF_CSRF_SECRET_KEY'] = app.secret_key


# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Initialize login manager
login = LoginManager(app)
login.init_app(app)


# Connect to postgres AWS RDS DB
cur = postgresConnect()


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


# For personal profile decoration!
# @app.route('/user/<username>')
# def profile(username):


@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def home():
    search_form = SearchForm()
    session['search_query'] = search_form.search.data
    if request.method == 'POST':
        return redirect((url_for('search_results')))
    return render_template('home.html', search_form=search_form)


@app.route('/search', methods=['GET', 'POST'])
def search_results(page=0):

    search_form = SearchForm()
    search_term = search_form.search.data

    if not exact_recipe_match(search_term, cur):
        return redirect('/')
    return redirect((url_for('compare_recipes', search_term=search_term,
                     page=page)))


@app.route('/search/<search_term>', methods=['GET'])
def compare_recipes(search_term, page=0, Np=20):

    search_form = SearchForm()
    sort_by = request.args.get('sort_by')
    page = int(request.args.get('page'))

    if not exact_recipe_match(search_term, cur):
        return redirect('/')

    # Get top 199 most similar recipes (of this page)
    results = content_based_search(search_term, cur)

    # Disentangle reference recipe and similar recipes
    reference_recipe = results.iloc[0]
    results = results.iloc[1::, :]

    # Select only the top Np recipes for one page
    results = results[(0+page*Np):((page+1)*Np)]

    # Sort by similarity, sustainability or rating
    results = hf.sort_search_results(results, sort_by)

    # Single variables are more conventient in HTML
    ratings = results['ratings']
    emissions = results['emissions']
    similarity = results['similarity']

    # make figures
    bp = ap.bar_compare_emissions(reference_recipe, results, sort_by=sort_by)

    return render_template('results.html',
                           reference_recipe=reference_recipe,
                           results=results,
                           ratings=ratings,
                           emissions=emissions,
                           similarity=similarity,
                           search_form=search_form,
                           search_term=search_term,
                           page=page,
                           bp=bp)


@app.route('/about', methods=['GET', 'POST'])
def about():
    search_form = SearchForm()
    search_term = search_form.search.data

    if search_term:
        if not exact_recipe_match(search_term, cur):
            return redirect('about.html', search_form=search_form)
        return redirect((url_for('compare_recipes', search_term=search_term)))
    return render_template('about.html', search_form=search_form)


@app.route('/profile')
def profile():
    # TODO
    # This will include a user's personal recommendations etc.
    return render_template('profile.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():

    reg_form = RegistrationForm()

    # Update database if validation success
    if reg_form.validate_on_submit():
        username = reg_form.username.data
        password = reg_form.password.data

        # Hash password
        # Automatically uses many iterations and adds salt for protection!
        hashed_pswd = pbkdf2_sha512.hash(password)

        # Add username & hashed password to DB
        user = User(username=username, password=hashed_pswd)
        db.session.add(user)
        db.session.commit()

        flash('Registered successfully. Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html', form=reg_form)


@app.route("/signin", methods=['GET', 'POST'])
def login():

    login_form = LoginForm()

    # Allow login if validation success
    if login_form.validate_on_submit():
        user_object = User.query.filter_by(
                        username=login_form.username.data).first()
        login_user(user_object)
        return redirect(url_for('home'))

    return render_template('signin.html', form=login_form)


@app.route("/logout", methods=['GET'])
def logout():
    logout_user()
    flash('You have logged out successfully', 'success')
    return redirect(url_for('home'))


if __name__ == '__main__':
    if debug:
        app.debug = True
    else:
        app.debug = False
    app.run()

# eof
