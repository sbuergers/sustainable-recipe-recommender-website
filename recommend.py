from psycopg2 import sql
import pandas as pd


def content_based_search(search_term, cur):
    '''
    DESCRIPTION:
        return the 200 most similar recipes to the url defined
        in <search term> based on cosine similarity in the "categories"
        space of the epicurious dataset.
    INPUT:
    search_term (str): url identifier for recipe (in recipes['url'])

    cur (psycopg2 connection)

    OUTPUT:
    results (dataframe)
        Recipe dataframe similar to recipes, but
        containing only the Nsim most similar recipes to the
        input. Also contains additional column "similarity".
    '''
    # Select recipe IDs of 200 most similar recipes to reference (search_term)
    cur.execute(sql.SQL("""
                SELECT * FROM public.content_similarity200_ids AS csids
                WHERE "recipeID" = (
                    SELECT "recipesID" FROM public.recipes
                    WHERE url = %s)
                """).format(), [search_term])
    CS_ids = cur.fetchall()[0][1::]
    CS_ids = tuple([abs(int(CSid)) for CSid in CS_ids])

    # Also select the actual similarity scores
    cur.execute(sql.SQL("""
                SELECT * FROM public.content_similarity200
                WHERE "recipeID" = (
                    SELECT "recipesID" FROM public.recipes
                    WHERE url = %s)
                """).format(), [search_term])
    CS = cur.fetchall()[0][1::]
    CS = tuple([abs(float(s)) for s in CS])

    # Finally, select similar recipes themselves
    # Get only those columns I actually use to speed things up
    col_sel = [
        'recipesID', 'title', 'ingredients', 'rating', 'calories',
        'sodium', 'fat', 'protein', 'ghg', 'prop_ing', 'ghg_log10',
        'url', 'servings', 'index', 'image_url', 'perc_rating',
        'perc_sustainability'
               ]

    # I am aware there is a discrepancy between the column names in SQL
    # and python, which is rather ugly. It is on my todo list to fix
    # in the future.
    cur.execute(sql.SQL("""
                SELECT "recipesID", "title", "ingredients",
                    "rating", "calories", "sodium", "fat",
                    "protein", "emissions", "prop_ingredients",
                    "emissions_log10", "url", "servings", "recipe_rawid",
                    "image_url", "perc_rating", "perc_sustainability"
                FROM public.recipes
                WHERE "recipesID" IN %s
                """).format(), [CS_ids])
    recipes_sql = cur.fetchall()

    # Obtain a dataframe for further processing
    results = pd.DataFrame(recipes_sql, columns=col_sel)
    results['similarity'] = CS

    # Assign data types (sql output might be decimal, should
    # be float!)
    numerics = ['recipesID', 'rating', 'calories', 'sodium',
                'fat', 'protein', 'ghg', 'prop_ing', 'ghg_log10',
                'index', 'perc_rating', 'perc_sustainability',
                'similarity']
    strings = ['title', 'ingredients', 'url', 'servings', 'image_url']
    for num in numerics:
        results[num] = pd.to_numeric(results[num])
    for s in strings:
        results[s] = results[s].astype('str')

    return results


# eof
