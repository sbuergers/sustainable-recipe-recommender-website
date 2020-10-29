""" main flask routes """

# Flask modules and forms
from flask import render_template, request, redirect, url_for
from flask import session
from flask_login import login_required, current_user

# User made modules
import application.main.helper_functions as hf
import application.main.altair_plots as ap
from application.main.forms import SearchForm
from application.sql_queries import Sql_queries

# Database
from application import db
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

    # No exact match found
    sq = Sql_queries(db.session)
    if sq.exact_recipe_match(search_term) is False:
        return redirect(url_for('main.search_results'))

    # Get params
    search_form = SearchForm()
    sort_by = request.args.get('sort_by')
    page = request.args.get('page')
    if page:
        page = int(page)
    else:
        page = 0
    bookmark = request.args.get('bookmark')

    # Add recipe to cookbook
    if bookmark:
        if current_user.is_anonymous:
            return redirect(url_for('auth.signin'))
        sq.add_to_cookbook(current_user.userID, bookmark)

    # Get top 199 most similar recipes
    results = sq.content_based_search(search_term)

    # Disentangle reference recipe and similar recipes
    ref_recipe = results.iloc[0]
    results = results.iloc[1::, :]

    # Select only the top Np recipes for one page
    results = results[(0+page*Np):((page+1)*Np)]

    # Retrieve or predict user ratings
    user_results = sq.query_user_ratings(current_user.userID, results['url'])
    user_ratings = hf.predict_user_ratings(user_results)

    # Sort by similarity, sustainability or rating
    results = hf.sort_search_results(results, sort_by)

    # Pass ratings & emissions jointly for ref recipe and results
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
                           user_ratings=user_ratings,
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

    # Get liked recipes
    sq = Sql_queries(db.session)
    cookbook = sq.query_cookbook(current_user.userID)

    # Sort by similarity, sustainability or rating
    sort_by = request.args.get('sort_by')
    cookbook = hf.sort_search_results(cookbook, sort_by)

    # Variables to sort by
    user_ratings = hf.predict_user_ratings(cookbook)
    avg_ratings = list(cookbook['perc_rating'].values)
    emissions = [v for v in cookbook['perc_sustainability'].values]

    # TODO Make figures

    return render_template('profile.html',
                           search_form=search_form,
                           cookbook=cookbook,
                           user_ratings=user_ratings,
                           avg_ratings=avg_ratings,
                           emissions=emissions)


# eof
