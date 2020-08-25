import pandas as pd
import numpy as np
# import datetime as dt


# Load recipe data review data
recipes = pd.read_csv(r'./data/recipes_sql.csv', index_col=0,
                      dtype={
                        'title': str,
                        'ingredients': str,
                        'directions': str,
                        'categories': str,
                        'date': str,              # should probably be datetime
                        'desc': str,
                        'rating': np.float64,
                        'calories': np.float64,
                        'sodium': np.float64,
                        'fat': np.float64,
                        'protein': np.float64,
                        'ghg': np.float64,
                        'prop_ing': np.float64,
                        'ghg_log10': np.float64,
                        'url': str,
                        'servings': str,
                        'index': np.int64,
                        'image_url': str,
                        'rating_count': np.int64
                      })

# Load review data
reviews = pd.read_csv(r'./data/reviews_sql.csv', index_col=0)

# Load recommendation model information
CS_ids = pd.read_csv(r'./data/content_similarity_200_ids.csv', index_col=0)
CS = pd.read_csv(r'./data/content_similarity_200.csv', index_col=0)


def content_based_search(search_term):
    '''
    DESCRIPTION:
        return the 200 most similar recipes to the url defined
        in <search term> based on cosine similarity in the "categories"
        space of the epicurious dataset (i.e. recipes data frame).
    INPUT:
    search_term (str)
        url identifier for recipe (in recipes['url'])
    OUTPUT:
    results (dataframe)
        Recipe dataframe similar to recipes, but
        containing only the Nsim most similar recipes to the
        input. Also contains additional column "similarity".
    '''
    # obtain IDs of similar recipes
    recipe_id = recipes.index[recipes['url'] == search_term].values
    similar_recipe_ids = abs(CS_ids.loc[recipe_id, :]).values

    # prepare output dataframe
    results = recipes.loc[similar_recipe_ids[0], :]
    results['similarity'] = CS.loc[recipe_id, :].values[0]

    return results

# eof
