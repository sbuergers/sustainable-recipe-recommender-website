"""
Unit tests for sql_queries.py
"""
import pytest
import sqlalchemy
from application import create_app
from dotenv import load_dotenv

load_dotenv('.env')


# FIXTURES
@pytest.fixture
def app():
    """ Instantiate app context """
    app = create_app(testing=True, debug=False)
    app_context = app.app_context()
    app_context.push()
    yield app
    app_context.pop()


@pytest.fixture
def pg(app):
    """ DB connection and testing query parameters """
    from application import db
    from application.sql_queries import Sql_queries
    pg = Sql_queries(db.session)
    pg.search_term = 'pineapple-shrimp-noodle-bowls'
    pg.fuzzy_search_term = 'chicken'
    pg.random_search_term = r'124 9i2oehf lkaj1iojk>,/1?/"490_£"'
    pg.phrase_search_term = 'vegan cookies'
    pg.sql_inj1 = "''; SELECT true; --"
    pg.sql_inj2 = "'; SELECT true; --"
    pg.userID = 2
    return pg


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
            pg.phrase_search(pg.phrase_search_term,
                             N=pg.sql_inj1)

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
        assert result[0:10] == (563, 2326, 343, 19957, 927,
                                141, 426, 2034, 13011, 29678)

        # sql injections
        with pytest.raises(IndexError):
            pg.query_content_similarity_ids(pg.sql_inj1)
        with pytest.raises(IndexError):
            pg.query_content_similarity_ids(pg.sql_inj2)

    def test_query_content_similarity(self, pg):
        # normal querries
        result = pg.query_content_similarity(pg.search_term)
        assert result[0:10] == (1.0, 0.452267, 0.43301266, 0.4166667,
                                0.41602513, 0.41247895, 0.41247895,
                                0.4082483, 0.40089187, 0.3952847)

        # sql injections
        with pytest.raises(IndexError):
            pg.query_content_similarity(pg.sql_inj1)
        with pytest.raises(IndexError):
            pg.query_content_similarity(pg.sql_inj2)

    def test_query_similar_recipes(self, pg):
        CS_ids = pg.query_content_similarity_ids(pg.search_term)
        result = pg.query_similar_recipes(CS_ids[0:2])
        assert len(result) == 2

    def test_content_based_search(self, pg):
        result = pg.content_based_search(pg.search_term)
        assert result.iloc[0]['similarity'] == 1.
        assert result.iloc[1]['similarity'] > 0.45

    def test_search_recipes(self, pg):
        # TODO what is being tested here?
        pg.content_based_search(pg.search_term)
        pg.fuzzy_search(pg.fuzzy_search_term)

    def test_query_cookbook(self, pg):
        result = pg.query_cookbook(pg.userID)
        assert result['username'][0] == 'test_user123'
        assert len(result) < 50
        result = pg.query_cookbook(999999999)
        assert len(result) == 0

# eof
