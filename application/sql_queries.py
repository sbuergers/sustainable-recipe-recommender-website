""" Class for advanced SQL queries without DB changes """
import pandas as pd
from sqlalchemy import text, bindparam, String, Integer, Numeric


class Sql_queries():

    def __init__(self, session):
        """
        Make DB connection via session object available to all queries
        session: (Flask-)SQLAlchemy session object
        """
        self.session = session

    def fuzzy_search(self, search_term, search_column="url", N=160):
        """
        DESCRIPTION:
            Searches in recipes table column url for strings that include the
            search_term. If none do, returns the top N results ordered
            by edit distance in ascending order.
        INPUT:
            search_term (str): String to look for in search_column
            search_column (str): Column to search (default="url")
            N (int): Max number of results to return
        OUTPUT:
            results (list of RowProxy objects): query results
        """
        # Most similar urls by edit distance that actually contain the
        # search_term
        query = text(
            """
            SELECT "recipesID", "title", "url", "perc_rating",
                "perc_sustainability", "review_count", "image_url",
                "emissions", "prop_ingredients",
                LEVENSHTEIN("url", :search_term) AS "rank"
            FROM public.recipes
            WHERE "url" LIKE :search_term_like
            ORDER BY "rank" ASC
            LIMIT :N
            """,
            bindparams=[
                bindparam('search_term', value=search_term, type_=String),
                bindparam('search_term_like', value='%'+search_term+'%',
                          type_=String),
                bindparam('N', value=N, type_=Integer)
            ]
        )
        results = self.session.execute(query).fetchall()

        # If no results contain the search_term
        if not results:
            query = text(
                """
                SELECT "recipesID", "title", "url", "perc_rating",
                    "perc_sustainability", "review_count", "image_url",
                    "emissions", "prop_ingredients",
                    LEVENSHTEIN("url", :search_term) AS "rank"
                FROM public.recipes
                ORDER BY "rank" ASC
                LIMIT :N
                """,
                bindparams=[
                    bindparam('search_term', value=search_term, type_=String),
                    bindparam('N', value=N, type_=Integer)
                ]
            )
            results = self.session.execute(query).fetchall()
        return results

    def phrase_search(self, search_term, N=160):
        """
        DESCRIPTION:
            Searches in table recipes in combined_tsv column using tsquery
            - a tsvector column in DB table recipes combining title and
            categories.
        INPUT:
            search_term (str): Search term
            N (int): Max number of results to return
        OUTPUT:
            results (list of RowProxy objects): DB query result
        """
        query = text(
            """
            SELECT "recipesID", "title", "url", "perc_rating",
                "perc_sustainability", "review_count", "image_url",
                "emissions", "prop_ingredients",
                ts_rank_cd(combined_tsv, query) AS rank
            FROM public.recipes,
                websearch_to_tsquery('simple', :search_term) query
            WHERE query @@ combined_tsv
            ORDER BY rank DESC
            LIMIT :N
            """,
            bindparams=[
                bindparam('search_term', value=search_term, type_=String),
                bindparam('N', value=N, type_=Integer)
            ]
        )
        results = self.session.execute(query).fetchall()
        return results

    def free_search(self, search_term, N=160):
        """
        DESCRIPTION:
            Parent function for searching recipes freely. At the moment
            it only calls phrase_search. But having this function makes
            it easier to extend in the future.
        INPUT:
            search_term (str)
            N (int): Max number of results to return
        OUTPUT:
            results (list of RowProxy objects): DB query result
        NOTES:
            See https://www.postgresql.org/docs/12/textsearch-controls.html
            for details on postgres' search functionalities.
        """
        results = self.phrase_search(search_term, N=N)
        if not results:
            results = self.fuzzy_search(search_term, N=N-len(results))
        return results

    def query_content_similarity_ids(self, search_term):
        """
        DESCRIPTION:
            Searches in connected postgres DB for a search_term in
            'url' column and returns recipeIDs of similar recipes based
            on content similarity.
        INPUT:
            search_term (str): Search term
        OUTPUT:
            CS_ids (tuple): Content based similarity ID vector ordered by
                similarity in descending order
        """
        query = text(
            """
            SELECT * FROM public.content_similarity200_ids
            WHERE "recipeID" = (
                SELECT "recipesID" FROM public.recipes
                WHERE "url" = :search_term)
            """,
            bindparams=[
                bindparam('search_term', value=search_term, type_=String)
            ]
        )
        CS_ids = self.session.execute(query).fetchall()[0][1::]
        CS_ids = tuple([abs(int(CSid)) for CSid in CS_ids])
        return CS_ids

    def query_content_similarity(self, search_term):
        """
        DESCRIPTION:
            Searches in connected postgres DB for a search_term in
            'url' and returns content based similarity.
        INPUT:
            search_term (str): Search term
        OUTPUT:
            CS (tuple): Content based similarity vector ordered by
                similarity in descending order
        """
        query = text(
            """
            SELECT * FROM public.content_similarity200
            WHERE "recipeID" = (
                SELECT "recipesID" FROM public.recipes
                WHERE url = :search_term)
            """,
            bindparams=[
                bindparam('search_term', value=search_term, type_=String)
            ]
        )
        CS = self.session.execute(query).fetchall()[0][1::]
        CS = tuple([abs(float(s)) for s in CS])
        return CS

    def query_similar_recipes(self, CS_ids):
        """
        DESCRIPTION:
            fetch recipe information of similar recipes based on the recipe IDs
            given by CS_ids
        INPUT:
            CS_ids (tuple): Tuple of recipe IDs
        OUTPUT:
            recipes_sql (list of RowProxy objects): DB query result
        """
        query = text(
            """
            SELECT "recipesID", "title", "ingredients",
                "rating", "calories", "sodium", "fat",
                "protein", "emissions", "prop_ingredients",
                "emissions_log10", "url", "servings", "recipe_rawid",
                "image_url", "perc_rating", "perc_sustainability",
                "review_count"
            FROM public.recipes
            WHERE "recipesID" IN :CS_ids
            """,
            bindparams=[
                bindparam('CS_ids', value=CS_ids, type_=Numeric)
            ]
        )
        recipes_sql = self.session.execute(query).fetchall()
        return recipes_sql

    def exact_recipe_match(self, search_term):
        '''
        DESCRIPTION:
            Return True if search_term is in recipes table of
            cur database, False otherwise.
        '''
        query = text(
            """
            SELECT * FROM public.recipes
            WHERE "url" = :search_term
            """,
            bindparams=[
                bindparam('search_term', value=search_term, type_=String)
            ]
        )
        if self.session.execute(query).fetchall():
            return True
        else:
            return False

    def content_based_search(self, search_term):
        '''
        DESCRIPTION:
            return the 200 most similar recipes to the url defined
            in <search term> based on cosine similarity in the "categories"
            space of the epicurious dataset.
        INPUT:
            search_term (str): url identifier for recipe (in recipes['url'])
        OUTPUT:
            results (dataframe): Recipe dataframe similar to recipes, but
                containing only the Nsim most similar recipes to the input.
                Also contains additional column "similarity".
        '''
        # Select recipe IDs of 200 most similar recipes to reference
        CS_ids = self.query_content_similarity_ids(search_term)

        # Also select the actual similarity scores
        CS = self.query_content_similarity(search_term)

        # Finally, select similar recipes themselves
        # Get only those columns I actually use to speed things up
        # Note that column names are actually different in sql and pandas
        # So if you want to adjust this, adjust both!
        # TODO: Make column names similar in pandas and sql!
        col_sel = [
                'recipesID', 'title', 'ingredients', 'rating', 'calories',
                'sodium', 'fat', 'protein', 'emissions', 'prop_ing',
                'emissions_log10', 'url', 'servings', 'index', 'image_url',
                'perc_rating', 'perc_sustainability', 'review_count'
                    ]
        recipes_sql = self.query_similar_recipes(CS_ids)

        # Obtain a dataframe for further processing
        results = pd.DataFrame(recipes_sql, columns=col_sel)

        # Add similarity scores to correct recipes (using recipesID again)
        temp = pd.DataFrame({'CS_ids': CS_ids, 'similarity': CS})
        results = results.merge(temp, left_on='recipesID',
                                right_on='CS_ids', how='left')

        # Assign data types (sql output might be decimal, should
        # be float!)
        numerics = ['recipesID', 'rating', 'calories', 'sodium',
                    'fat', 'protein', 'emissions', 'prop_ing',
                    'emissions_log10', 'index', 'perc_rating',
                    'perc_sustainability', 'similarity', 'review_count']
        strings = ['title', 'ingredients', 'url', 'servings', 'image_url']
        for num in numerics:
            results[num] = pd.to_numeric(results[num])
        for s in strings:
            results[s] = results[s].astype('str')

        # Order results by similarity
        results = results.sort_values(by='similarity', ascending=False)

        return results

    def search_recipes(self, search_term, N=160):
        """
        DESCRIPTION:
            Does a free search for recipes based on user's search term. If an
            exact match exists, does a content based search and returns the
            resulting DataFrame.
        INPUT:
            search_term (str): Search term input by user into search bar
            N (int): Max number of results to return
        OUTPUT:
            df (pd.DataFrame): DataFrame with recipes as rows
        """
        outp = self.free_search(search_term, N)

        if outp[0][2] == search_term:
            return self.content_based_search(search_term)

        col_names = ["recipesID", "title", "url", "perc_rating",
                     "perc_sustainability", "review_count", "image_url",
                     "ghg", "prop_ingredients", "rank"]

        results = pd.DataFrame(outp, columns=col_names)

        # Assign data types (sql output might be decimal, should
        # be float!)
        numerics = ['recipesID', 'perc_rating', 'ghg', 'prop_ingredients',
                    'perc_rating', 'perc_sustainability', 'review_count']
        strings = ['title', 'url', 'image_url']
        for num in numerics:
            results[num] = pd.to_numeric(results[num])
        for s in strings:
            results[s] = results[s].astype('str')

        # Order results by rank / edit_dist
        results = results.sort_values(by='rank', ascending=False)
        return results

    def query_cookbook(self, userID):
        """
        DESCRIPTION:
            Creates a pandas dataframe containing all recipes the given
            user has liked / added to the cookbook.
        INPUT:
            userID (Integer)
        OUTPUT:
            cookbook (pd.DataFrame)
        """
        query = text(
            """
            SELECT u."userID", u.username,
                l.created, l.rating,
                r.title, r.url, r.perc_rating, r.perc_sustainability,
                r.review_count, r.image_url, r.emissions, r.prop_ingredients
                FROM users u
                JOIN likes l ON (u.username = l.username)
                JOIN recipes r ON (l."recipesID" = r."recipesID")
            WHERE u."userID" = :userID
            ORDER BY l.rating
            """,
            bindparams=[
                bindparam('userID', value=userID, type_=Integer)
            ]
        )
        recipes = self.session.execute(query).fetchall()

        # Convert to DataFrame
        col_sel = ["userID", "username", "created", "user_rating",
                   "recipe_title", "url", "perc_rating", "perc_sustainability",
                   "review_count", "image_url", "emissions", "prop_ingredients"]
        results = pd.DataFrame(recipes, columns=col_sel)

        # Assign data types
        numerics = ['userID', 'user_rating', 'perc_rating',
                    'perc_sustainability', 'review_count', 'emissions',
                    'prop_ingredients']
        strings = ['username', 'recipe_title', 'url', 'image_url']
        datetimes = ['created']
        for num in numerics:
            results[num] = pd.to_numeric(results[num])
        for s in strings:
            results[s] = results[s].astype('str')
        for dt in datetimes:
            results[dt] = pd.to_datetime(results[dt])
        return results


# eof
