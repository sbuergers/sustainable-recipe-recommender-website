"""
Test script for flask routes.

Useful links:
https://flask.palletsprojects.com/en/1.1.x/testing/
https://pythonhosted.org/Flask-Testing/
https://www.patricksoftwareblog.com/testing-a-flask-application-using-pytest/
https://stackoverflow.com/questions/17375340/testing-code-that-requires-a-flask-app-or-request-context
"""
import pytest
from flask import url_for, request
from application import create_app
from bs4 import BeautifulSoup


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
def test_client(app):
    test_client = app.test_client()
    test_request_context = app.test_request_context()
    test_request_context.push()
    yield test_client
    test_request_context.pop()


@pytest.fixture
def pg(app):
    """ DB connection """
    from application import db
    from application.sql_queries import Sql_queries
    pg = Sql_queries(db.session)
    return pg


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
    user.userID = 2
    return user


# HELPER FUNCTIONS
def signup(test_client, email, username, password):
    return test_client.post(url_for('auth.signup'), data={
        'email': email,
        'username': username,
        'password': password
        }, follow_redirects=True)


def login(test_client, username, password):
    return test_client.post(url_for('auth.signin'), data={
        'username': username,
        'password': password
        }, follow_redirects=True)


def logout(test_client):
    return test_client.get(url_for('auth.logout'), follow_redirects=True)


def route_meta_tag(r):
    """
    Given the html output from a test_client get or post call
    (in r.data), retrieve the route name given in the meta tags.
    """
    soup = BeautifulSoup(r.data, features="html.parser")
    return soup.find_all("meta", attrs={'name': 'route'})[0]['content']


# TESTS
class TestRoutesMain:

    def test_home(self, test_client):
        """ Endpoint checks """

        r = test_client.get('/')
        assert r.status_code == 200
        r = test_client.get(url_for('main.home'))
        assert r.status_code == 200

    def test_search_results(self, test_client, par):
        """ Endpoint checks """

        for search_term in par.search_terms:
            if search_term:
                r = test_client.get(url_for('main.search_results',
                                            search_term=search_term),
                                    follow_redirects=True)
                assert r.status_code == 200

    def test_compare_recipes(self, test_client, par):
        """ Endpoint checks """

        search_term = par.recipe_tag

        # Default request
        r = test_client.get(url_for('main.compare_recipes',
                                    search_term=search_term),
                            data={},
                            follow_redirects=True)
        assert r.status_code == 200
        assert request.args.get('sort_by') is None
        assert request.args.get('page') is None

        # Specifying <sort_by> and <page> args
        for sort_by in par.sort_bys:
            for page in range(0, 1):
                r = test_client.get(url_for('main.compare_recipes',
                                    search_term=search_term),
                                    data={'sort_by': sort_by,
                                          'page': page},
                                    follow_redirects=True)
                assert r.status_code == 200

    def test_cookbook(self, test_client, user):
        """ Endpoint check """

        # Logged out (redirects to signin)
        r = test_client.get(url_for('main.cookbook'), follow_redirects=True)
        assert r.status_code == 200
        assert b'Sign in' in r.data

        # Logged in (accesses profile)
        login(test_client, user.name, user.pw)
        r = test_client.get(url_for('main.cookbook'), follow_redirects=True)
        assert r.status_code == 200
        assert b'Cookbook' in r.data

    def test_profile(self, test_client, user):
        """ Endpoint check """

        # Logged out (redirects to signin)
        r = test_client.get(url_for('main.profile'), follow_redirects=True)
        assert r.status_code == 200
        assert b'Sign in' in r.data

        # Logged in (accesses profile)
        login(test_client, user.name, user.pw)
        r = test_client.get(url_for('main.profile'), follow_redirects=True)
        assert r.status_code == 200
        assert b'Search for sustainable recipes' not in r.data

    def test_about(self, test_client):
        """ Endpoint check """

        r = test_client.get(url_for('main.about'), follow_redirects=True)
        assert r.status_code == 200

    def test_blog(self, test_client):
        """ Endpoint check """

        r = test_client.get(url_for('main.blog'), follow_redirects=True)
        assert r.status_code == 200

    def test_add_or_remove_bookmark(self, test_client, pg, user, par):
        '''
        We can get here from various routes - the user
        clicks on the bookmark (or un-bookmark) button and this
        view handles the database changes and then redirects
        back to the route we came from ("origin").
        '''
        search_term = par.recipe_tag
        login(test_client, user.name, user.pw)

        # Check if recipe is in cookbook
        bookmark_status = pg.is_in_cookbook(user.userID, search_term)

        # Create 'search_query' variable in session object
        with test_client.session_transaction() as sess:
            sess['search_query'] = search_term

        # coming from main.compare_recipes
        r = test_client.get(url_for('main.add_or_remove_bookmark',
                                    bookmark=search_term,
                                    origin='main.compare_recipes'),
                            follow_redirects=True)

        # Are we redirected back correctly?
        assert route_meta_tag(r) == "main.compare_recipes"

        # The bookmark status should have changed, did it?
        assert bookmark_status != pg.is_in_cookbook(user.userID, search_term)
        bookmark_status = pg.is_in_cookbook(user.userID, search_term)

        # coming from main.search_results
        with test_client.session_transaction() as sess:
            # use only part of search_term so multiple results are found
            sess['search_query'] = search_term.split('-')[0]

        r = test_client.get(url_for('main.add_or_remove_bookmark',
                                    bookmark=search_term,
                                    origin='main.search_results'),
                            follow_redirects=True)

        # Are we redirected back correctly?
        assert route_meta_tag(r) == "main.search_results"

        # The bookmark status should have changed, did it?
        assert bookmark_status != pg.is_in_cookbook(user.userID, search_term)
        bookmark_status = pg.is_in_cookbook(user.userID, search_term)

        # coming from main.profile
        r = test_client.get(url_for('main.add_or_remove_bookmark',
                                    bookmark=search_term,
                                    origin='main.cookbook'),
                            follow_redirects=True)

        # Are we redirected back correctly?
        assert route_meta_tag(r) == "main.cookbook"

        # The bookmark status should have changed, did it?
        assert bookmark_status != pg.is_in_cookbook(user.userID, search_term)
        bookmark_status = pg.is_in_cookbook(user.userID, search_term)

    def test_like_recipe(self, test_client, pg, par):
        """
        Check that routing works and rating changes correctly.
        """

        # Ensure recipe rating is 3 (default = unrated)
        pg.rate_recipe(user.userID, par.recipe_tag, 3)
        rating = pg.query_user_ratings(user.userID, [par.recipe_tag])\
                   .user_rating[0]
        assert rating == 3

        # logged out: Redirect to auth.login
        test_client.get(url_for('auth.logout'), follow_redirects=True)

        origins = ['main.cookbook', 'main.search_results',
                   'main.compare_recipes']
        sort_bys = ['Sustainability']*3
        for (origin, sort_by, search_term) in zip(origins, sort_bys,
                                                  par.search_terms):
            r = test_client.post(url_for('main.like_recipe',
                                         recipe_url=par.recipe_tag,
                                         origin=origin,
                                         sort_by=sort_by,
                                         search_query=search_term),
                                 follow_redirects=True)
            assert r.status_code == 200
            assert route_meta_tag(r) == 'auth.login'

        # Assert rating is still 3
        rating = pg.query_user_ratings(user.userID, [par.recipe_tag])\
                   .user_rating[0]
        assert rating == 3

        # logged in: Redirect back to origin
        login(test_client, user.name, user.pw)

        for (origin, sort_by, search_term) in zip(origins, sort_bys,
                                                  par.search_terms):
            pg.rate_recipe(user.userID, par.recipe_tag, 3)
            r = test_client.post(url_for('main.like_recipe',
                                         recipe_url=par.recipe_tag,
                                         origin=origin,
                                         sort_by=sort_by,
                                         search_query=search_term),
                                 follow_redirects=True)
            assert r.status_code == 200
            assert route_meta_tag(r) == origin
            rating = pg.query_user_ratings(user.userID, [par.recipe_tag])\
                       .user_rating[0]
            assert rating == 5

    def test_dislike_recipe(self, test_client, pg, par):
        """
        Check that routing works and rating changes correctly.
        """

        # Ensure recipe rating is 3 (default = unrated)
        pg.rate_recipe(user.userID, par.recipe_tag, 3)
        rating = pg.query_user_ratings(user.userID, [par.recipe_tag])\
                   .user_rating[0]
        assert rating == 3

        # logged out: Redirect to auth.login
        test_client.get(url_for('auth.logout'), follow_redirects=True)

        origins = ['main.cookbook', 'main.search_results',
                   'main.compare_recipes']
        sort_bys = ['Sustainability']*3
        for (origin, sort_by, search_term) in zip(origins, sort_bys,
                                                  par.search_terms):
            r = test_client.post(url_for('main.dislike_recipe',
                                         recipe_url=par.recipe_tag,
                                         origin=origin,
                                         sort_by=sort_by,
                                         search_query=search_term),
                                 follow_redirects=True)
            assert r.status_code == 200
            assert route_meta_tag(r) == 'auth.login'

        # Assert rating is still 3
        rating = pg.query_user_ratings(user.userID, [par.recipe_tag])\
                   .user_rating[0]
        assert rating == 3

        # logged in: Redirect back to origin
        login(test_client, user.name, user.pw)

        for (origin, sort_by, search_term) in zip(origins, sort_bys,
                                                  par.search_terms):
            pg.rate_recipe(user.userID, par.recipe_tag, 3)
            r = test_client.post(url_for('main.dislike_recipe',
                                         recipe_url=par.recipe_tag,
                                         origin=origin,
                                         sort_by=sort_by,
                                         search_query=search_term),
                                 follow_redirects=True)
            assert r.status_code == 200
            assert route_meta_tag(r) == origin
            rating = pg.query_user_ratings(user.userID, [par.recipe_tag])\
                       .user_rating[0]
            assert rating == 1

    def test_unlike_recipe(self, test_client, pg, par):
        """
        Check that routing works and rating changes correctly.
        """

        # Ensure recipe rating is 1 (disliked)
        pg.rate_recipe(user.userID, par.recipe_tag, 1)
        rating = pg.query_user_ratings(user.userID, [par.recipe_tag])\
                   .user_rating[0]
        assert rating == 1

        # logged out: Redirect to auth.login
        test_client.get(url_for('auth.logout'), follow_redirects=True)

        origins = ['main.cookbook', 'main.search_results',
                   'main.compare_recipes']
        sort_bys = ['Sustainability']*3
        for (origin, sort_by, search_term) in zip(origins, sort_bys,
                                                  par.search_terms):
            r = test_client.post(url_for('main.unlike_recipe',
                                         recipe_url=par.recipe_tag,
                                         origin=origin,
                                         sort_by=sort_by,
                                         search_query=search_term),
                                 follow_redirects=True)
            assert r.status_code == 200
            assert route_meta_tag(r) == 'auth.login'

        # Assert rating is still 3
        rating = pg.query_user_ratings(user.userID, [par.recipe_tag])\
                   .user_rating[0]
        assert rating == 1

        # logged in: Redirect back to origin
        login(test_client, user.name, user.pw)

        for (origin, sort_by, search_term) in zip(origins, sort_bys,
                                                  par.search_terms):
            pg.rate_recipe(user.userID, par.recipe_tag, 1)
            r = test_client.post(url_for('main.unlike_recipe',
                                         recipe_url=par.recipe_tag,
                                         origin=origin,
                                         sort_by=sort_by,
                                         search_query=search_term),
                                 follow_redirects=True)
            assert r.status_code == 200
            assert route_meta_tag(r) == origin
            rating = pg.query_user_ratings(user.userID, [par.recipe_tag])\
                       .user_rating[0]
            assert rating == 3


class TestRoutesAuth:

    def test_signup(self, test_client):
        """ Endpoint check """

        r = test_client.get(url_for('auth.signup'), follow_redirects=True)
        assert r.status_code == 200

    def test_signin(self, test_client):
        """ Endpoint check, failed credentials check """

        r = test_client.get(url_for('auth.signin'), follow_redirects=True)
        assert r.status_code == 200

        r = login(test_client, user.name + 'x290fdsjkl', user.pw)
        assert b'Username or password is incorrect' in r.data

        r = login(test_client, user.name, user.pw + 'x13fhszlfo')
        assert b'Username or password is incorrect' in r.data

    def test_logout(self, test_client, user):
        """ Enpoint check """
        # TODO...

    def test_terms_and_conditions(self, test_client, user):
        """ Enpoint check """
        # TODO...

    def test_reset_password_request(self, test_client, user):
        """ Enpoint check """
        # TODO...

    def test_reset_password(self, test_client, user):
        """ Enpoint check """
        # TODO...

    def test_login_logout(self, test_client, user):
        """ Test navbar changes appropriate to logins status """

        # Logged in
        login(test_client, user.name, user.pw)
        r = test_client.get(url_for('main.home'), follow_redirects=True)
        assert b'Cookbook' in r.data
        assert b'Login' not in r.data

        # Logged out
        test_client.get(url_for('auth.logout'), follow_redirects=True)
        r = test_client.get(url_for('main.home'), follow_redirects=True)
        assert b'Cookbook' not in r.data
        assert b'Login' in r.data

    def test_password_reset(self, test_client):
        """ Test reset_password_request() and reset_password() """
        # TODO ...
        pass


# eof
