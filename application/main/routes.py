""" main flask routes """

# Flask modules and forms
from flask import render_template, request, redirect, url_for
from flask import session
from flask_login import login_required

# User made modules
import application.main.helper_functions as hf
import application.main.altair_plots as ap
from application.main.forms import SearchForm
from application.main.sql_queries import Sql_queries

# Database
from application import db
from application.main import bp
from application.models import User


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

    # navbar-search
    search_form = SearchForm()
    search_term = search_form.search.data
    if search_term:
        redirect(url_for('main.search_results'))

    return render_template('about.html', search_form=search_form)


# insecure, avoid user input!
@bp.route('/blog', methods=['GET', 'POST'])
def blog():

    # navbar-search
    search_form = SearchForm()
    search_term = search_form.search.data
    if search_term:
        redirect(url_for('main.search_results'))

    return render_template('blog.html', search_form=search_form)


@bp.route('/profile')
@login_required
def profile():

    # navbar-search
    search_form = SearchForm()
    search_term = search_form.search.data
    if search_term:
        redirect(url_for('main.search_results'))

    # TODO profile search

    # TODO query data for profile content: Cookbook recipes

    return render_template('profile.html',
                           search_form=search_form)


# eof
