""" main flask routes """

# Flask modules and forms
from flask import render_template, request, redirect, url_for
from flask import session
from flask_login import login_required, current_user

# User made modules
import application.main.helper_functions as hf
import application.main.altair_plots as ap
from application.main.forms import SearchForm, EmptyForm
from application.sql_queries import Sql_queries

# Database
from application import db
from application.main import bp


# Use only one Sql_queries instance
sq = Sql_queries(db.session)


@bp.route('/')
@bp.route('/home', methods=['GET', 'POST'])
def home():
    search_form = SearchForm()
    if request.method == 'POST':
        session['search_query'] = search_form.search.data
        return redirect((url_for('main.search_results')))
    return render_template('home.html', search_form=search_form)


@bp.route('/search', methods=['GET', 'POST'])
def search_results():

    # We either get the search_term from the SearchForm, or we
    # use the "old" query saved in session
    search_form = SearchForm()
    like_form = EmptyForm()
    if request.method == 'POST':
        search_term = search_form.search.data
        session['search_query'] = search_form.search.data
    else:
        search_term = session['search_query']

    # exact match? Suggest alternatives!
    if sq.exact_recipe_match(search_term):
        return redirect(url_for('main.compare_recipes',
                                search_term=search_term))
    # fuzzy search
    results = sq.search_recipes(search_term)

    if len(results) > 0:

        # Add recipe to cookbook
        hf.add_or_remove_bookmark(sq)

        # Retrieve or predict user ratings
        # TODO: Currently user_ratings isn't used at all
        # - put in helper fun, used in compare_recipes and search_results
        if current_user.is_authenticated:
            urls = list(results['url'].values)

            # Bookmarked recipes
            df_bookmarks = sq.query_bookmarks(current_user.userID, urls)
            results = results.merge(df_bookmarks, how='left', on='recipesID')
            results['bookmarked'].fillna(False, inplace=True)

        # ratings and emissions need to be passed separately for JS
        ratings = list(results['perc_rating'].values)
        emissions = [v for v in results['perc_sustainability'].values]

        return render_template('explore.html',
                               search_form=search_form,
                               like_form=like_form,
                               results=results,
                               ratings=ratings,
                               emissions=emissions)
    return redirect('/')


@bp.route('/search/<search_term>', methods=['GET'])
def compare_recipes(search_term, page=0, Np=20):

    # No exact match found
    if sq.exact_recipe_match(search_term) is False:
        return redirect(url_for('main.search_results'))

    # Get params and set defaults
    search_form = SearchForm()
    like_form = EmptyForm()
    sort_by = request.args.get('sort_by')
    if not sort_by:
        sort_by = 'Similarity'
    page = request.args.get('page')
    if page:
        page = int(page)
    else:
        page = 0

    # Add recipe to cookbook
    hf.add_or_remove_bookmark(sq)

    # Get top 199 most similar recipes
    results = sq.content_based_search(search_term)

    # Retrieve or predict user ratings
    # TODO: Currently user_ratings isn't used at all
    # - put in helper fun, used in compare_recipes and search_results
    if current_user.is_authenticated:
        urls = list(results['url'].values)

        # User ratings
        user_results = sq.query_user_ratings(current_user.userID, urls)
        user_ratings = hf.predict_user_ratings(user_results)

        # Bookmarked recipes
        df_bookmarks = sq.query_bookmarks(current_user.userID, urls)
        results = results.merge(df_bookmarks, how='left', on='recipesID')
        results['bookmarked'].fillna(False, inplace=True)
    else:
        user_ratings = None

    # Disentangle reference recipe and similar recipes
    ref_recipe = results.iloc[0]
    results = results.iloc[1::, :]

    # Select only the top Np recipes for one page
    results = results[(0+page*Np):((page+1)*Np)]

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
                           like_form=like_form,
                           search_form=search_form,
                           search_term=search_term,
                           page=page,
                           bp=bp)


@bp.route('/profile', methods=['GET'])
@login_required
def profile():

    # navbar-search
    search_form = SearchForm()
    search_term = search_form.search.data
    if search_term:
        redirect(url_for('main.search_results'))

    # Like/Unlike form
    like_form = EmptyForm()

    # Remove bookmark
    hf.add_or_remove_bookmark(sq)

    # TODO profile search

    # Get bookmarked recipes
    cookbook = sq.query_cookbook(current_user.userID)

    # Sort by similarity, sustainability or rating
    sort_by = request.args.get('sort_by')
    if not sort_by:
        sort_by = 'Sustainability'
    cookbook = hf.sort_search_results(cookbook, sort_by)

    # TODO create separate route for personalized recommendations, see
    # https://github.com/sbuergers/sustainable-recipe-recommender-website/issues/3#issuecomment-717503064
    # user_ratings = hf.predict_user_ratings(cookbook)

    # Variables to sort by
    avg_ratings = list(cookbook['perc_rating'].values)
    emissions = [v for v in cookbook['perc_sustainability'].values]

    # TODO Make figures

    return render_template('profile.html',
                           search_form=search_form,
                           cookbook=cookbook,
                           avg_ratings=avg_ratings,
                           emissions=emissions,
                           like_form=like_form)


@bp.route('/like/<recipe_url>', methods=['POST'])
@login_required
def like_recipe(recipe_url):
    form = EmptyForm()
    if form.validate_on_submit():
        sort_by = request.form.get('sort_by')
        sq.rate_recipe(current_user.userID, recipe_url, 5)
        return redirect(url_for('main.profile', sort_by=sort_by))
    else:
        return redirect(url_for('main.profile', sort_by=sort_by))


@bp.route('/dislike/<recipe_url>', methods=['POST'])
@login_required
def dislike_recipe(recipe_url):
    form = EmptyForm()
    if form.validate_on_submit():
        sort_by = request.form.get('sort_by')
        sq.rate_recipe(current_user.userID, recipe_url, 1)
        return redirect(url_for('main.profile', sort_by=sort_by))
    else:
        return redirect(url_for('main.profile', sort_by=sort_by))


@bp.route('/unlike/<recipe_url>', methods=['POST'])
@login_required
def unlike_recipe(recipe_url):
    form = EmptyForm()
    if form.validate_on_submit():
        sort_by = request.form.get('sort_by')
        sq.rate_recipe(current_user.userID, recipe_url, 3)
        return redirect(url_for('main.profile', sort_by=sort_by))
    else:
        return redirect(url_for('main.profile', sort_by=sort_by))


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


# eof
