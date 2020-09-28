"""
Unit tests for sql_queries.py
"""
import pytest
import psycopg2 as ps

# Make sure parent directory is added to search path before
# importing sql_queries!
import os
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

# Now I can import sql_queries
import sql_queries
from dotenv import load_dotenv

load_dotenv('.env')


# I cannot simply define an __init__ method - pytest does
# not treat TestSqlQueries as an actual class, it's more of
# a way to group test functions together. Instead I can
# create a fixture "pg" doing the same thing.
@pytest.fixture
def pg():
    pg = sql_queries.postgresConnection()
    pg.search_term = 'pineapple-shrimp-noodle-bowls'
    pg.fuzzy_search_term = 'chicken'
    pg.random_search_term = r'124 9i2oehf lkaj1iojk>,/1?/"490_£"'
    pg.phrase_search_term = 'vegan cookies'
    pg.search_column = 'combined_tsv'
    pg.sql_inj1 = "''; SELECT true; --"
    pg.sql_inj2 = "'; SELECT true; --"
    return pg


class TestSqlQueries:

    def test_connect(self, pg):
        assert pg.conn.closed == 0

    def test_fuzzy_search(self, pg):
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
        with pytest.raises(ps.errors.InvalidTextRepresentation):
            pg.fuzzy_search(pg.fuzzy_search_term, N=pg.sql_inj1)

    def test_phrase_search(self, pg):
        # normal querries
        result = pg.phrase_search(pg.search_column, pg.phrase_search_term, N=2)
        assert len(result) == 2

        # sql injections
        assert len(pg.phrase_search(pg.search_column, pg.sql_inj1, N=2)) == 0
        assert len(pg.phrase_search(pg.search_column, pg.sql_inj2, N=2)) == 0
        with pytest.raises(ps.errors.InvalidTextRepresentation):
            pg.phrase_search(pg.search_column, pg.phrase_search_term,
                             N=pg.sql_inj1)

    def test_free_search(self, pg):
        # normal querries
        result = pg.free_search(pg.phrase_search_term, N=2)
        assert len(result) >= 2

        # sql injections
        assert len(pg.free_search(pg.sql_inj1, N=2)) == 2
        assert len(pg.free_search(pg.sql_inj2, N=2)) == 2
        with pytest.raises(ps.errors.InvalidTextRepresentation):
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


# eof
