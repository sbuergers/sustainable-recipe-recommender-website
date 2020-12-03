# Flask modules and forms
from flask import request, redirect, url_for
from flask_login import current_user


def sort_search_results(results, sort_by):
    '''
    DESCRIPTION:
        Sorts results dataframe by column specified in sort_by
    INPUT:
        results (DataFrame): Subset of recipes DataFrame containing
            similar recipes to reference recipe to be diplayed

        sort_by (string): What metric to sort rows by. Can be one of
            ['similarity', 'sustainability', 'rating'], or a user
            specified column name. default = 'similarity'
    OUTPUT:
        Updated results dataframe sorted as requested.
    '''
    # When sort_by is empty, simply return input dataframe
    # This can happen when the URL is tempered with manually
    if not sort_by:
        sort_by = 'similarity'

    # Otherwise try to sort
    sort_by = sort_by.lower()
    if sort_by == 'similarity':
        return results
    if sort_by == 'sustainability':
        return results.sort_values(by='emissions', ascending=True)
    if sort_by == 'rating':
        return results.sort_values(by='rating', ascending=False)
    else:
        return results.sort_values(by=sort_by, ascending=False)


def predict_user_ratings(df):
    '''
    TODO: Implement algo. Placeholder fills in 5 for all ratings

    DESCRIPTION:
        Takes DataFrame with output from Sql_queries.query_cookbook()
        and predicts missing user ratings.
    INPUT:
        df (pd.DataFrame)
    OUTPUT:
        user_ratings (List): Updated ratings column converted to percentages
    '''
    df['user_rating'].fillna(value=5, inplace=True)
    user_ratings = [round(v/5*100) for v in df['user_rating'].values]
    return user_ratings


def add_or_remove_bookmark(sq):
    '''
    DESCRIPTION:
        Checks if a GET request contains a 'bookmark', meaning that a user
        has clicked the 'bookmark' button of a recipe. If so, either adds
        or deletes the recipe from the user's cookbook. Can be called in
        any route in routes.py.
    INPUT:
        sq: sql_queries object (see sql_queries.py)
    OUTPUT:
        None
    '''
    bookmark = request.args.get('bookmark')
    if bookmark:
        if current_user.is_anonymous:
            return redirect(url_for('auth.signin'))
        if sq.is_in_cookbook(current_user.userID, bookmark):
            sq.remove_from_cookbook(current_user.userID, bookmark)
        else:
            sq.add_to_cookbook(current_user.userID, bookmark)


def get_favorite_recipes(df, N):
    '''
    DESCRIPTION:
        retrieves the names of the N most favorite recipes. For now favorite
        recipes are those with a "thumbs up", i.e. rating equal to 5.
    INPUT:
        df (pandas.DataFrame): "cookbook" dataframe (see profile in routes.py)
        N (Integer): Maximum number of titles to return
    OUTPUT:
        titles (List of strings): List of favorite recipe titles
    '''
    return list(
        df.sort_values(by='user_rating', ascending=False)
        .loc[df['user_rating'] == 5, 'title']
    )[0:N]


# eof
