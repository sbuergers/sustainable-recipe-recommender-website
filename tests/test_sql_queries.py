"""
Unit tests for sql_queries.py
"""
import pytest
import sqlalchemy
import pandas as pd
from application import create_app
from dotenv import load_dotenv

load_dotenv(".env")


# FIXTURES
@pytest.fixture
def app():
    """Instantiate app context"""
    app = create_app(testing=True, debug=False)
    app_context = app.app_context()
    app_context.push()
    yield app
    app_context.pop()


@pytest.fixture
def pg(app):
    """DB connection and testing query parameters"""
    from application import db
    from application.sql_queries import Sql_queries

    pg = Sql_queries(db.session)
    pg.search_term = "pineapple-shrimp-noodle-bowls"
    pg.url = "pineapple-shrimp-noodle-bowls"
    pg.url_bookmark = "pineapple-shrimp-noodle-bowls"
    pg.urls_exist = [pg.url, "cold-sesame-noodles-12715"]
    pg.urls_dont_exist = ["i-am-not-a-recipe-link", "neither-am-i"]
    pg.fuzzy_search_term = "chicken"
    pg.random_search_term = r'124 9i2oehf lkaj1iojk>,/1?/"490_£"'
    pg.phrase_search_term = "vegan cookies"
    pg.sql_inj1 = "''; SELECT true; --"
    pg.sql_inj2 = "'; SELECT true; --"
    pg.userID = 3
    pg.recipesID = 563  # 'pineapple-shrimp-noodle-bowls'
    pg.dummy_name = "dummy938471948"
    pg.dummy_email = "dummyEmail@dummy12394821.com"
    pg.dummy_password = "dummyPassword129482"
    return pg


# HELPER FUNCTIONS
def create_dummy_account(pg):
    """Create dummy account with liked and bookmarked recipes"""

    from application.models import User
    from passlib.hash import pbkdf2_sha512
    import datetime

    # If user entry already exists, do nothing, otherwise create it
    user = User.query.filter_by(username=pg.dummy_name).first()

    if not user:
        user = User(
            username=pg.dummy_name,
            password=pbkdf2_sha512.hash(pg.dummy_password),
            email=pg.dummy_email,
            confirmed=False,
            created_on=datetime.datetime.utcnow(),
            optin_news=True,
        )
        pg.session.add(user)
        pg.session.commit()
        user = User.query.filter_by(username=pg.dummy_name).first()

    # Add item to cookbook
    pg.add_to_cookbook(user.userID, pg.url)

    # Like a recipe
    pg.rate_recipe(user.userID, pg.url, 5)

    user = User.query.filter_by(username=pg.dummy_name).first()
    assert user.email == pg.dummy_email


# TESTS
class TestSqlQueries:
    def test_fuzzy_search(self, app, pg):

        # normal querries
        result = pg.fuzzy_search(pg.fuzzy_search_term, N=2)  # substr of "url"
        assert len(result) == 2
        assert pg.fuzzy_search_term in result[0][2]
        assert pg.fuzzy_search_term in result[1][2]
        result = pg.fuzzy_search(pg.random_search_term, N=2)  # not in "url"
        assert len(result) == 2

        # sql injections
        assert len(pg.fuzzy_search(pg.sql_inj1, N=2)) == 2
        assert len(pg.fuzzy_search(pg.sql_inj2, N=2)) == 2
        with pytest.raises(sqlalchemy.exc.DataError):
            pg.fuzzy_search(pg.fuzzy_search_term, N=pg.sql_inj1)

    def test_phrase_search(self, pg):

        # normal querries
        result = pg.phrase_search(pg.phrase_search_term, N=2)
        assert len(result) == 2

        # sql injections
        assert len(pg.phrase_search(pg.sql_inj1, N=2)) == 0
        assert len(pg.phrase_search(pg.sql_inj2, N=2)) == 0
        with pytest.raises(sqlalchemy.exc.DataError):
            pg.phrase_search(pg.phrase_search_term, N=pg.sql_inj1)

    def test_free_search(self, pg):

        # normal querries
        result = pg.free_search(pg.phrase_search_term, N=2)
        assert len(result) >= 2

        # sql injections
        assert len(pg.free_search(pg.sql_inj1, N=2)) == 2
        assert len(pg.free_search(pg.sql_inj2, N=2)) == 2
        with pytest.raises(sqlalchemy.exc.DataError):
            pg.free_search(pg.phrase_search_term, N=pg.sql_inj1)

    def test_query_content_similarity_ids(self, pg):

        # normal querries
        result = pg.query_content_similarity_ids(pg.search_term)
        assert result[0:10] == (
            563,
            2326,
            343,
            19957,
            927,
            141,
            426,
            2034,
            13011,
            29678,
        )

        # sql injections
        with pytest.raises(IndexError):
            pg.query_content_similarity_ids(pg.sql_inj1)
        with pytest.raises(IndexError):
            pg.query_content_similarity_ids(pg.sql_inj2)

    def test_query_content_similarity(self, pg):

        # normal querries
        result = pg.query_content_similarity(pg.search_term)
        assert result[0:10] == (
            1.0,
            0.452267,
            0.43301266,
            0.4166667,
            0.41602513,
            0.41247895,
            0.41247895,
            0.4082483,
            0.40089187,
            0.3952847,
        )

        # sql injections
        with pytest.raises(IndexError):
            pg.query_content_similarity(pg.sql_inj1)
        with pytest.raises(IndexError):
            pg.query_content_similarity(pg.sql_inj2)

    def test_query_similar_recipes(self, pg):

        CS_ids = pg.query_content_similarity_ids(pg.search_term)
        result = pg.query_similar_recipes(CS_ids[0:2])
        assert len(result) == 2

    def test_exact_recipe_match(self, pg):

        assert pg.exact_recipe_match(pg.url) is True
        assert pg.exact_recipe_match(pg.urls_dont_exist[0]) is False

    def test_content_based_search(self, pg):

        result = pg.content_based_search(pg.search_term)
        assert result.iloc[0]["similarity"] == 1.0
        assert result.iloc[1]["similarity"] > 0.45

    def test_search_recipes(self, pg):
        # TODO test proper function of N parameter

        # exact match
        res = pg.search_recipes(pg.search_term)
        assert res is not None
        assert res["title"].tolist()[0].lower() == pg.search_term.replace("-", " ")

        # fuzzy match
        pg.search_recipes(pg.fuzzy_search_term)
        assert res is not None
        assert res["title"].tolist()[0].lower() != pg.fuzzy_search_term.replace(
            "-", " "
        )

    def test_query_all_recipe_emissions(self, pg):

        df = pg.query_all_recipe_emissions()
        assert sorted(list(df.columns.values)) == [
            "emissions",
            "emissions_log10",
            "recipesID",
            "title",
            "url",
        ]
        assert df.shape[0] > 36000

    def test_query_cookbook(self, pg):

        result = pg.query_cookbook(pg.userID)
        assert result["username"][0] == "asdfjlq;weruioasdnf"
        assert len(result) < 50
        result = pg.query_cookbook(999999999)
        assert len(result) == 0

    def test_query_bookmarks(self, pg):

        # un-bookmark url
        pg.remove_from_cookbook(pg.userID, pg.url_bookmark)
        df = pg.query_bookmarks(pg.userID, [pg.url_bookmark])
        assert df.empty

        # bookmarked url
        pg.add_to_cookbook(pg.userID, pg.url_bookmark)
        df = pg.query_bookmarks(pg.userID, [pg.url_bookmark])
        assert df["bookmarked"][0]

    def test_is_in_cookbook(self, pg):

        # there is an entry
        result = pg.is_in_cookbook(pg.userID, pg.url)
        assert result

        # there is no entry
        result = pg.is_in_cookbook(pg.userID, pg.url + "123")
        assert not result
        result = pg.is_in_cookbook(pg.userID + 999999999, pg.url)
        assert not result

    def test_add_to_and_delete_from_cookbook(self, pg):
        """Tests both <remove_from_cookbook> and <add_to_cookbook>"""

        # Try adding existing entry
        result = pg.add_to_cookbook(pg.userID, pg.url)
        assert result == "Cookbook entry already exists"

        # Remove entry
        result = pg.remove_from_cookbook(pg.userID, pg.url)
        assert result == "Removed recipe from cookbook successfully"
        result = pg.remove_from_cookbook(pg.userID, pg.url)
        assert result == "Recipe was not bookmarked to begin with"

        # Add new entry
        result = pg.add_to_cookbook(pg.userID, pg.url)
        assert result == "Cookbook entry added successfully"

        # Add new entry with invalid userID or url
        result = pg.add_to_cookbook(pg.userID, pg.url + "123")
        assert result == "UserID or recipe url invalid"
        result = pg.add_to_cookbook(pg.userID + 999999999, pg.url)
        assert result == "UserID or recipe url invalid"

    def test_query_user_ratings(self, pg):

        # Query existing entries in likes table
        df = pg.query_user_ratings(pg.userID, pg.urls_exist + pg.urls_dont_exist)
        assert type(df) == pd.core.frame.DataFrame
        assert not df.empty

        # Query non-existing entries in likes table
        df = pg.query_user_ratings(pg.userID, pg.urls_dont_exist)
        assert df.empty

    def test_rate_recipe(self, pg):

        from application.models import User, Recipe

        # Change recipe rating to 4
        pg.rate_recipe(pg.userID, pg.url, 4)
        df = pg.query_user_ratings(pg.userID, [pg.url])
        assert df.loc[df["recipesID"] == pg.recipesID, "user_rating"].values == 4

        # Change rating to 5
        pg.rate_recipe(pg.userID, pg.url, 5)
        df = pg.query_user_ratings(pg.userID, [pg.url])
        assert df.loc[df["recipesID"] == pg.recipesID, "user_rating"].values == 5

        # Add rating for new account (entry does not exist yet)
        create_dummy_account(pg)
        user = User.query.filter_by(username=pg.dummy_name).first()
        pg.rate_recipe(user.userID, pg.urls_exist[1], 5)
        recipesID = Recipe.query.filter_by(url=pg.urls_exist[1]).first().recipesID
        df = pg.query_user_ratings(user.userID, [pg.urls_exist[1]])
        assert df.loc[df["recipesID"] == recipesID, "user_rating"].values == 5
        pg.delete_account(user.userID)

    def test_delete_account(self, pg):
        """First create account, then check if deletion works"""

        from application.models import User

        # Create dummy user account and delete it
        create_dummy_account(pg)
        userID = User.query.filter_by(username=pg.dummy_name).first().userID
        assert userID > 0

        msg = pg.delete_account(userID)
        user = User.query.filter_by(username=pg.dummy_name).first()
        assert user is None
        assert msg == "Removed user account successfully"

        # Try removing user that doesn't exist
        msg = pg.delete_account(userID)
        assert msg == "User not found. Nothing was removed."

    def test_change_newsletter_subscription(self, pg):
        """Can we successfully change newsleetter subscription status?"""

        from application.models import User

        # Change newsletter subscription back and forth
        for i in range(0, 2):
            old_status = User.query.filter_by(userID=pg.userID).first().optin_news
            msg = pg.change_newsletter_subscription(pg.userID)
            new_status = User.query.filter_by(userID=pg.userID).first().optin_news
            assert old_status != new_status
            if new_status:
                assert msg == 'Changed newsletter subscription to "subscribed"'
            else:
                assert msg == 'Changed newsletter subscription to "unsubscribed"'

        # User does not exist
        msg = pg.change_newsletter_subscription(999999999999)
        assert msg == "User not found"


# eof
