"""
Test script for flask application.

Useful links:
https://flask.palletsprojects.com/en/1.1.x/testing/
https://pythonhosted.org/Flask-Testing/
https://www.patricksoftwareblog.com/testing-a-flask-application-using-pytest/
https://stackoverflow.com/questions/17375340/testing-code-that-requires-a-flask-app-or-request-context
"""
import pytest

# Make sure parent directory is added to search path before
# importing create_app from app.py
import os
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from app import create_app
from flask import url_for


@pytest.fixture
def test_client():
    app = create_app(testing=True, debug=False)
    test_client = app.test_client()
    app_context = app.app_context()
    test_request_context = app.test_request_context()
    app_context.push()
    test_request_context.push()
    yield test_client
    test_request_context.pop()
    app_context.pop()


def test_home(test_client):
    r = test_client.get('/')
    assert r.status_code == 200
    r = test_client.get('/home')
    assert r.status_code == 200


def test_search_results(test_client):
    search_terms = ['', 'chicken', 'pineapple-shrimp-noodle-bowls']
    for search_term in search_terms:
        if search_term == '':
            res = test_client.post(url_for('search_results'),
                                   json={'search_term': search_term},
                                   follow_redirects=True)
            assert res.status_code == 200
        else:
            res = test_client.post(url_for('search_results'),
                                   json={'search_term': search_term,
                                         'page': 1},
                                   follow_redirects=True)
            assert res.status_code == 200


# eof
