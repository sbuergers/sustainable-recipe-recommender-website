"""
Unit tests for sql_queries.py
"""
import pytest

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
# create a fixture pg doing the same thing.
@pytest.fixture
def pg():
    pg = sql_queries.postgresConnection()
    pg.search_term = 'pineapple-shrimp-noodle-bowls'
    pg.fuzzy_search_term = 'chicken'
    return pg


class TestSqlQueries:

    def test_connect(self, pg):
        assert pg.conn.closed == 0

    def test_fuzzy_search(self, pg):
        result = pg.fuzzy_search(pg.fuzzy_search_term, N=2)
        assert len(result) == 2
        assert pg.fuzzy_search_term in result[0][2]
        assert pg.fuzzy_search_term in result[1][2]

    def test_query_content_similarity_ids(self, pg):
        result = pg.query_content_similarity_ids(pg.search_term)
        assert result[0:10] == (563, 2326, 343, 19957, 927,
                                141, 426, 2034, 13011, 29678)

    def test_query_content_similarity(self, pg):
        result = pg.query_content_similarity(pg.search_term)
        assert result[0:10] == (1.0, 0.452267, 0.43301266, 0.4166667,
                                0.41602513, 0.41247895, 0.41247895,
                                0.4082483, 0.40089187, 0.3952847)

    def test_query_similar_recipes(self, pg):
        CS_ids = pg.query_content_similarity_ids(pg.search_term)
        result = pg.query_similar_recipes(CS_ids[0:2])
        assert len(result) == 2

    def test_content_based_search(self, pg):
        result = pg.content_based_search(pg.search_term)
        assert result.iloc[0]['similarity'] == 1.
        assert result.iloc[1]['similarity'] > 0.45

    def test_search_recipes(self, pg):
        pg.content_based_search(pg.search_term)
        pg.fuzzy_search(pg.fuzzy_search_term)


# eof
