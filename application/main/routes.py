""" Flask routes """

# Flask modules and forms
from flask import render_template, request, redirect, url_for, flash
from flask import session
from flask_login import login_user, current_user, logout_user
from flask_login import login_required

# Password hashing
from passlib.hash import pbkdf2_sha512

# User made modules
import application.main.helper_functions as hf
import application.main.altair_plots as ap
from application.main.wtform_fields import RegistrationForm, LoginForm,\
                                           SearchForm
from application.main.sql_queries import Sql_queries

# Database
from application import db
from application.main.models import User
from application.main import bp


@bp.route('/')
@bp.route('/home', methods=['GET', 'POST'])
def home():
    search_form = SearchForm()
    session['search_query'] = search_form.search.data
    if request.method == 'POST':
        return redirect((url_for('main.search_results')))
    return render_template('home.html', search_form=search_form)


@bp.route('/search', methods=['GET', 'POST'])
def search_results(page=0):
    search_form = SearchForm()
    search_term = search_form.search.data

    # exact match? Suggest alternatives!
    sq = Sql_queries(db.session)
    if sq.exact_recipe_match(search_term):
        return redirect(url_for('main.compare_recipes',
                                search_term=search_term,
                                page=page))
    # fuzzy search
    results = sq.search_recipes(search_term)

    if len(results) > 0:

        # ratings and emissions need to be passed separately for JS
        ratings = list(results['perc_rating'].values)
        emissions = [v for v in results['perc_sustainability'].values]

        return render_template('explore.html',
                               search_form=search_form,
                               results=results,
                               ratings=ratings,
                               emissions=emissions)
    return redirect('/')


@bp.route('/search/<search_term>', methods=['GET'])
def compare_recipes(search_term, page=0, Np=20):
    search_form = SearchForm()
    sort_by = request.args.get('sort_by')
    page = request.args.get('page')
    # TODO is this needed?
    if page:
        page = int(page)
    else:
        page = 0

    sq = Sql_queries(db.session)
    if sq.exact_recipe_match(search_term) is False:
        return redirect(url_for('main.search_results'))

    # Get top 199 most similar recipes (of this page)
    results = sq.content_based_search(search_term)

    # Disentangle reference recipe and similar recipes
    ref_recipe = results.iloc[0]
    results = results.iloc[1::, :]

    # Select only the top Np recipes for one page
    results = results[(0+page*Np):((page+1)*Np)]

    # Sort by similarity, sustainability or rating
    results = hf.sort_search_results(results, sort_by)

    # Pass ratings & emissions jointly for ref recipe and results
    # TODO this is very ugly, do this more succinctly earlier on!
    ratings = list(results['perc_rating'].values)
    ratings = [ref_recipe['perc_rating']] + ratings
    emissions = [v for v in results['perc_sustainability'].values]
    emissions = [ref_recipe['perc_sustainability']] + emissions
    similarity = [round(v*100) for v in results['similarity'].values]

    # make figures
    bp = ap.bar_compare_emissions(ref_recipe, results, sort_by=sort_by)

    return render_template('results.html',
                           reference_recipe=ref_recipe,
                           results=results,
                           ratings=ratings,
                           emissions=emissions,
                           similarity=similarity,
                           search_form=search_form,
                           search_term=search_term,
                           page=page,
                           bp=bp)


@bp.route('/about', methods=['GET', 'POST'])
def about():
    search_form = SearchForm()
    search_term = search_form.search.data
    if search_term:
        redirect(url_for('main.search_results'))

    return render_template('about.html', search_form=search_form)


# insecure, avoid user input!
@bp.route('/blog', methods=['GET', 'POST'])
def blog():
    search_form = SearchForm()
    search_term = search_form.search.data
    if search_term:
        redirect(url_for('main.search_results'))

    return render_template('blog.html', search_form=search_form)


@bp.route('/profile')
@login_required
def profile():
    search_form = SearchForm()
    search_term = search_form.search.data
    if search_term:
        redirect(url_for('main.search_results'))

    return render_template('profile.html', search_form=search_form)


@bp.route('/signup', methods=['GET', 'POST'])
def signup():

    reg_form = RegistrationForm()

    # Update database if validation success
    if reg_form.validate_on_submit():
        username = reg_form.username.data
        password = reg_form.password.data
        email = reg_form.email.data

        # Hash password and email
        # Automatically uses many iterations and adds salt for protection!
        hashed_pswd = pbkdf2_sha512.hash(password)
        hashed_email = pbkdf2_sha512.hash(email)

        # Add username & hashed password to DB
        user = User(username=username,
                    password=hashed_pswd,
                    email=hashed_email)
        db.session.add(user)
        db.session.commit()

        flash('Registered successfully. Please login.', 'success')
        return redirect(url_for('main.signin'))

    return render_template('signup.html', reg_form=reg_form)


@bp.route("/signin", methods=['GET', 'POST'])
def signin():

    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    login_form = LoginForm()

    # Allow login if validation success
    if login_form.validate_on_submit():
        user_object = User.query.filter_by(
                        username=login_form.username.data).first()
        login_user(user_object, remember=False)
        return redirect(url_for('main.home'))

    return render_template('signin.html', login_form=login_form)


@bp.route("/logout", methods=['GET'])
@login_required
def logout():
    logout_user()
    flash('You have logged out successfully.', 'success')
    return redirect(url_for('main.home'))


# eof
