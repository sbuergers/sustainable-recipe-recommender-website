"""
Unit tests for sql_queries.py
"""

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


class TestSqlQueries:

    def __init__(self):
        self.pg = sql_queries.postgresConnection()
        self.search_term = 'pineapple-shrimp-noodle-bowls'
        self.fuzzy_search_term = 'chicken'

    def test_connect(self):
        assert self.pg.conn.closed == 0

    def test_fuzzy_search(self):
        result = self.pg.fuzzy_search(self.fuzzy_search_term, N=2)
        assert len(result) == 2
        assert self.fuzzy_search_term in result[0][2]
        assert self.fuzzy_search_term in result[1][2]

    def test_query_content_similarity_ids(self):
        result = self.pg.query_content_similarity_ids(self.search_term)
        assert result[0:10] == (563, 2326, 343, 19957, 927,
                                141, 426, 2034, 13011, 29678)

    def test_query_content_similarity(self):
        result = self.pg.query_content_similarity(self.search_term)
        assert result[0:10] == (1.0, 0.452267, 0.43301266, 0.4166667,
                                0.41602513, 0.41247895, 0.41247895,
                                0.4082483, 0.40089187, 0.3952847)

    def test_query_similar_recipes(self):
        CS_ids = self.pg.query_content_similarity_ids(self.search_term)
        result = self.pg.query_similar_recipes(CS_ids[0:2])
        assert len(result) == 2

    def test_content_based_search(self):
        result = self.pg.content_based_search(self.search_term)
        assert result.iloc[0]['similarity'] == 1.
        assert result.iloc[1]['similarity'] > 0.45

    def test_search_recipes(self):
        self.test_content_based_search()
        self.test_fuzzy_search()


# eof
