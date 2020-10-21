"""
Test script for flask application.

Useful links:
https://flask.palletsprojects.com/en/1.1.x/testing/
https://pythonhosted.org/Flask-Testing/
https://www.patricksoftwareblog.com/testing-a-flask-application-using-pytest/
https://stackoverflow.com/questions/17375340/testing-code-that-requires-a-flask-app-or-request-context
"""
import pytest

from flask import url_for, request

# Make sure parent directory is added to search path before
# importing create_app from app.py
import os
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from application import create_app
from config import DevConfig
from wtform_fields import RegistrationForm, LoginForm


# FIXTURES
@pytest.fixture
def test_client():
    app = create_app(cfg=DevConfig)
    test_client = app.test_client()
    app_context = app.app_context()
    test_request_context = app.test_request_context()
    app_context.push()
    test_request_context.push()
    yield test_client
    test_request_context.pop()
    app_context.pop()


@pytest.fixture
def par():
    par.search_terms = ['', 'chicken', 'pineapple-shrimp-noodle-bowls']
    par.recipe_tag = 'pineapple-shrimp-noodle-bowls'
    par.sort_bys = ['Sustainability', 'Similarity', 'Rating']
    par.page = 1
    par.Np = 40
    return par


@pytest.fixture
def user():
    user.name = 'test_user123'
    user.pw = 'zvnwkf[ejDSdEvn;1wfj-'
    return user


# HELPER FUNCTIONS
def login(test_client, username, password):
    return test_client.post(url_for('signin'), data={
        'username': username,
        'password': password
        }, follow_redirects=True)


def logout(test_client):
    return test_client.get(url_for('logout'), follow_redirects=True)


# TESTS
def test_home(test_client):
    r = test_client.get('/')
    assert r.status_code == 200
    r = test_client.get('/home')
    assert r.status_code == 200


def test_search_results(test_client, par):
    for search_term in par.search_terms:
        if search_term == '':
            r = test_client.post(url_for('search_results'),
                                 data={'search_term': search_term},
                                 follow_redirects=True)
            assert r.status_code == 200
        else:
            r = test_client.post(url_for('search_results'),
                                 data={'search_term': search_term,
                                       'page': par.page},
                                 follow_redirects=True)
            assert r.status_code == 200


def test_compare_recipes(test_client, par):
    search_term = par.recipe_tag

    # Default request
    r = test_client.get(url_for('compare_recipes',
                        search_term=search_term),
                        data={},
                        follow_redirects=True)
    assert r.status_code == 200
    assert request.args.get('sort_by') is None
    assert request.args.get('page') is None

    # Specifying <sort_by> and <page> args
    for sort_by in par.sort_bys:
        for page in range(0, 1):
            r = test_client.get(url_for('compare_recipes',
                                search_term=search_term),
                                data={'sort_by': sort_by,
                                      'page': page},
                                follow_redirects=True)
            assert r.status_code == 200


def test_about(test_client):
    r = test_client.get(url_for('about'), follow_redirects=True)
    assert r.status_code == 200


def test_blog(test_client):
    r = test_client.get(url_for('blog'), follow_redirects=True)
    assert r.status_code == 200


def test_profile(test_client, user):
    r = test_client.get(url_for('profile'), follow_redirects=True)
    assert r.status_code == 200
    assert url_for('signin') == '/signin'
    login(test_client, user.name, user.pw)
    r = test_client.get(url_for('profile'), follow_redirects=True)
    assert url_for('profile') == '/profile'
    assert r.status_code == 200


def test_signup(test_client):
    r = test_client.get(url_for('signup'), follow_redirects=True)
    assert r.status_code == 200


def test_login(test_client):
    r = test_client.get(url_for('signin'), follow_redirects=True)
    assert r.status_code == 200

    r = login(test_client, user.name + 'x290fdsjkl', user.pw)
    assert b'Username or password is incorrect' in r.data

    r = login(test_client, user.name, user.pw + 'x13fhszlfo')
    assert b'Username or password is incorrect' in r.data


# TODO Why is this:
# For some reason I cannot use current_user.is_authenticated (always
# False), but I can assert whether login worked by checking the route
# endpoint for requests where a logged in user is required.
def test_login_logout(test_client, user):
    login(test_client, user.name, user.pw)
    test_client.get(url_for('profile'), follow_redirects=True)
    assert url_for('profile') == '/profile'
    r = test_client.get(url_for('logout'), follow_redirects=True)
    assert r.status_code == 200
    test_client.get(url_for('profile'), follow_redirects=True)
    assert url_for('signin') == '/signin'


# eof
