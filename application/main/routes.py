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
        if search_form.search.data:
            session['search_query'] = search_form.search.data
            return redirect((url_for('main.search_results',
                            search_term=session['search_query'])))
    return render_template('home.html', search_form=search_form)


@bp.route('/search/<search_term>', methods=['GET', 'POST'])
def search_results(search_term):

    like_form = EmptyForm()
    search_form = SearchForm()

    # exact match? Suggest alternatives!
    if sq.exact_recipe_match(search_term):
        return redirect(url_for('main.compare_recipes',
                                search_term=search_term))
    # fuzzy search
    results = sq.search_recipes(search_term)

    if len(results) > 0:

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


@bp.route('/recipe/<search_term>', methods=['GET', 'POST'])
def compare_recipes(search_term, Np=20):

    # No exact match found
    if sq.exact_recipe_match(search_term) is False:
        return redirect(url_for('main.search_results',
                                search_term=search_term))

    # Forms
    search_form = SearchForm()
    like_form = EmptyForm()

    # Sorting results
    sort_by = request.args.get('sort_by')
    if not sort_by:
        sort_by = 'Similarity'

    # Pagination
    page = request.args.get('page')
    page = int(page) if page else 0

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


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile(Np=20):

    # navbar-search
    search_form = SearchForm()

    # Like/Unlike form and bookmark form
    like_form = EmptyForm()
    bookmark_form = EmptyForm()

    # Pagination
    page = request.args.get('page')
    page = int(page) if page else 0

    # TODO profile search

    # Get bookmarked recipes
    cookbook = sq.query_cookbook(current_user.userID)

    # Descriptive statistics to show to user
    Nrecipes = cookbook.shape[0]
    Nliked = sum(cookbook['user_rating'] == 5)
    Ndisliked = sum(cookbook['user_rating'] == 1)
    fav_recipes = hf.get_favorite_recipes(cookbook, 3)
    fav_categ, fav_categ_cnt = hf.get_favorite_categories(cookbook, 7)
    mean_cookbook_emissions = round(sum(cookbook['emissions']) /
                                    (cookbook.shape[0]+0.00001), 2)
    recommendations = ['']  # TODO write helper func

    # Prepare figure data
    df_hist = sq.query_all_recipe_emissions()
    df_hist['reference'] = df_hist.url.isin(cookbook['url'])
    df_hist.rename(columns={'emissions_log10': 'log10(Emissions)',
                            'emissions': 'Emissions',
                            'title': 'Title'}, inplace=True)

    # Sort by similarity, sustainability or rating
    sort_by = request.args.get('sort_by')
    if not sort_by:
        sort_by = 'Sustainability'
    cookbook = hf.sort_search_results(cookbook, sort_by)
    Npages = cookbook.shape[0] // Np + 1

    # Select only the top Np recipes for one page
    cookbook = cookbook[(0+page*Np):((page+1)*Np)]

    # TODO create separate route for personalized recommendations, see
    # https://github.com/sbuergers/sustainable-recipe-recommender-website/issues/3#issuecomment-717503064
    # user_ratings = hf.predict_user_ratings(cookbook)

    # Variables to sort by
    avg_ratings = list(cookbook['perc_rating'].values)
    emissions = [v for v in cookbook['perc_sustainability'].values]

    # Make figures
    hist_title = "Emissions distribution of cookbook recipes"
    hist_emissions = ap.histogram_emissions(df_hist, hist_title)

    return render_template('profile.html',
                           search_form=search_form,
                           cookbook=cookbook,
                           Nrecipes=Nrecipes,
                           Nliked=Nliked,
                           Ndisliked=Ndisliked,
                           fav_recipes=fav_recipes,
                           fav_categ=fav_categ,
                           fav_categ_cnt=fav_categ_cnt,
                           mean_cookbook_emissions=mean_cookbook_emissions,
                           recommendations=recommendations,
                           avg_ratings=avg_ratings,
                           emissions=emissions,
                           like_form=like_form,
                           bookmark_form=bookmark_form,
                           page=page,
                           Npages=Npages,
                           hist_emissions=hist_emissions)


@bp.route('/add_or_remove_bookmark/<bookmark>/<origin>', methods=['GET'])
@login_required
def add_or_remove_bookmark(bookmark, origin):
    # TODO fix sort_by for main.compare_recipes and main.search_results
    hf.add_or_remove_bookmark(sq, bookmark)
    if origin == 'main.compare_recipes':
        search_term = session['search_query']
        return redirect(url_for(origin, search_term=search_term))
    elif origin == 'main.search_results':
        search_term = session['search_query']
        return redirect(url_for(origin, search_term=search_term,
                                sort_by='Sustainability'))
    elif origin == 'main.profile':
        sort_by = request.form.get('sort_by')
        return redirect(url_for(origin, sort_by=sort_by))
    return redirect(url_for('main.home'))


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


@bp.route('/about')
def about():
    search_form = SearchForm()
    return render_template('about.html', search_form=search_form)


# insecure, avoid user input!
@bp.route('/blog')
def blog():
    search_form = SearchForm()
    return render_template('blog.html', search_form=search_form)


# eof
