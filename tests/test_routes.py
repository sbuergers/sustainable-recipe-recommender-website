"""
Test script for flask routes.

Useful links:
https://flask.palletsprojects.com/en/1.1.x/testing/
https://pythonhosted.org/Flask-Testing/
https://www.patricksoftwareblog.com/testing-a-flask-application-using-pytest/
https://stackoverflow.com/questions/17375340/testing-code-that-requires-a-flask-app-or-request-context
"""
import pytest
from flask import url_for
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

    # TODO move parameters to par or user
    pg.url = 'pineapple-shrimp-noodle-bowls'
    pg.dummy_name = 'dummy938471948'
    pg.dummy_email = 'dummyEmail@dummy12394821.com'
    pg.dummy_password = 'dummyPassword129482'
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
    user.email = 'test123@email123.com'
    return user


# HELPER FUNCTIONS
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


def create_dummy_account(pg):
    """ Create dummy account with liked and bookmarked recipes """

    from application.models import User
    from passlib.hash import pbkdf2_sha512
    import datetime

    # If user entry already exists, do nothing, otherwise create it
    user = User.query.filter_by(username=pg.dummy_name).first()

    if not user:
        user = User(username=pg.dummy_name,
                    password=pbkdf2_sha512.hash(pg.dummy_password),
                    email=pg.dummy_email,
                    confirmed=False,
                    created_on=datetime.datetime.utcnow(),
                    optin_news=True)
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
class TestRoutesMain:

    def test_home(self, test_client, par):

        # Endpoint checks
        r = test_client.get('/')
        assert r.status_code == 200
        r = test_client.get(url_for('main.home'))
        assert r.status_code == 200

        # Post search terms
        endpoints = ['main.home', 'main.search_results',
                     'main.compare_recipes']
        for (search_term, endpoint) in zip(par.search_terms, endpoints):
            form_data = {'search': search_term}
            r = test_client.post(url_for('main.home'),
                                 follow_redirects=True, json=form_data)
            assert route_meta_tag(r) == endpoint

    def test_search_results(self, test_client, par):

        # Assess three different types of search terms
        endpoints = ['main.home', 'main.search_results',
                     'main.compare_recipes']
        for (search_term, endpoint) in zip(par.search_terms, endpoints):

            # An empty search_term yields 404
            if search_term:
                r = test_client.post(url_for('main.search_results',
                                             search_term=search_term),
                                     follow_redirects=True)
                assert route_meta_tag(r) == endpoint

    def test_compare_recipes(self, test_client, par):
        # TODO currently does not check if sorting or pagination works

        # Default request
        search_term = par.recipe_tag
        r = test_client.get(url_for('main.compare_recipes',
                                    search_term=search_term),
                            data={},
                            follow_redirects=True)
        assert route_meta_tag(r) == 'main.compare_recipes'

        # Specifying <sort_by> and <page> args
        for sort_by in par.sort_bys:
            for page in range(0, 1):
                r = test_client.get(url_for('main.compare_recipes',
                                    search_term=search_term),
                                    data={'sort_by': sort_by,
                                          'page': page},
                                    follow_redirects=True)
                assert route_meta_tag(r) == 'main.compare_recipes'

        # There is no exact recipe match
        search_term = par.search_terms[1]
        r = test_client.get(url_for('main.compare_recipes',
                                    search_term=search_term),
                            data={},
                            follow_redirects=True)
        assert route_meta_tag(r) == 'main.search_results'

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

    def test_profile(self, test_client, user, pg):

        from application.models import User

        # Logged out (redirects to signin)
        r = test_client.get(url_for('main.profile'), follow_redirects=True)
        assert r.status_code == 200
        assert b'Sign in' in r.data

        # Logged in (accesses profile)
        login(test_client, user.name, user.pw)
        r = test_client.get(url_for('main.profile'), follow_redirects=True)
        assert r.status_code == 200
        assert b'Search for sustainable recipes' not in r.data

        # Access profile route without verified email
        u = User.query.filter_by(userID=user.userID).first()
        u.confirmed = False
        pg.session.commit()
        r = test_client.post(url_for('main.profile'),
                             data={'submit_verify_email': True},
                             follow_redirects=True)
        assert b'Send verification email' in r.data
        assert b'Change newsletter subscription' not in r.data
        assert b'A verification link has been sent to your email address.' \
            in r.data

        # Access profile route with verified email
        u.confirmed = True
        pg.session.commit()
        r = test_client.post(url_for('main.profile'), follow_redirects=True)
        assert b'Send verification email' not in r.data
        assert b'Change newsletter subscription' in r.data

        # Newsletter subscription form
        for i in range(2):
            old_status = User.query.filter_by(userID=user.userID).first() \
                            .optin_news
            r = test_client.post(url_for('main.profile'),
                                 data={'submit_newsletter': True},
                                 follow_redirects=True)
            new_status = User.query.filter_by(userID=user.userID).first() \
                             .optin_news
            assert old_status != new_status
            assert route_meta_tag(r) == 'main.profile'

        # Create and login dummy account
        logout(test_client)
        create_dummy_account(pg)
        login(test_client, pg.dummy_name, pg.dummy_password)

        # Delete account form (invalid)
        userID = User.query.filter_by(username=pg.dummy_name).first().userID
        assert userID > 0
        r = test_client.post(url_for('main.profile'),
                             data={'username': pg.dummy_name + 'asdfjkl;',
                                   'submit_delete_account': True},
                             follow_redirects=True)
        user = User.query.filter_by(username=pg.dummy_name).first()
        assert user is not None
        assert route_meta_tag(r) == 'main.profile'

        # Delete account form (valid)
        userID = User.query.filter_by(username=pg.dummy_name).first().userID
        assert userID > 0
        form_data = {'username': pg.dummy_name,
                     'submit_delete_account': True}
        r = test_client.post(url_for('main.profile'),
                             follow_redirects=True, json=form_data)
        user = User.query.filter_by(username=pg.dummy_name).first()
        assert b'Your account has been deleted successfully.' in r.data
        assert user is None

        # TODO Redirectig home does not work,  why?!
        # assert route_meta_tag(r) == 'main.home'

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

        # coming from a random page that is not expected
        r = test_client.get(url_for('main.add_or_remove_bookmark',
                                    bookmark=search_term,
                                    origin='main.about'),
                            follow_redirects=True)
        assert route_meta_tag(r) == 'main.home'

    def test_like_recipe(self, test_client, pg, par):
        """
        Changes a recipe's user_rating to 5.
        We can get here from various routes - the user clicks on a
        like button and this view handles the database changes and
        then redirects back to the route we came from ("origin").
        """

        # Ensure recipe rating is 3 (default = unrated)
        pg.rate_recipe(user.userID, par.recipe_tag, 3)
        rating = pg.query_user_ratings(user.userID, [par.recipe_tag])\
                   .user_rating[0]
        assert rating == 3

        # logged out: Redirect to auth.signin
        logout(test_client)

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
            assert route_meta_tag(r) == 'auth.signin'

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

        # coming from a random page that is not expected
        r = test_client.post(url_for('main.like_recipe',
                                     recipe_url=par.recipe_tag,
                                     origin='main.about',
                                     sort_by=sort_by,
                                     search_query=search_term),
                             follow_redirects=True)
        assert route_meta_tag(r) == 'main.home'

    def test_dislike_recipe(self, test_client, pg, par):
        """
        Changes a recipe's user_rating to 1.
        We can get here from various routes - the user clicks on a
        like button and this view handles the database changes and
        then redirects back to the route we came from ("origin").
        """

        # Ensure recipe rating is 3 (default = unrated)
        pg.rate_recipe(user.userID, par.recipe_tag, 3)
        rating = pg.query_user_ratings(user.userID, [par.recipe_tag])\
                   .user_rating[0]
        assert rating == 3

        # logged out: Redirect to auth.signin
        logout(test_client)

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
            assert route_meta_tag(r) == 'auth.signin'

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

        # coming from a random page that is not expected
        r = test_client.post(url_for('main.dislike_recipe',
                                     recipe_url=par.recipe_tag,
                                     origin='main.about',
                                     sort_by=sort_by,
                                     search_query=search_term),
                             follow_redirects=True)
        assert route_meta_tag(r) == 'main.home'

    def test_unlike_recipe(self, test_client, pg, par):
        """
        Changes a recipe's user_rating to 3.
        We can get here from various routes - the user clicks on a
        like button and this view handles the database changes and
        then redirects back to the route we came from ("origin").
        """

        # Ensure recipe rating is 1 (disliked)
        pg.rate_recipe(user.userID, par.recipe_tag, 1)
        rating = pg.query_user_ratings(user.userID, [par.recipe_tag])\
                   .user_rating[0]
        assert rating == 1

        # logged out: Redirect to auth.signin
        logout(test_client)

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
            assert route_meta_tag(r) == 'auth.signin'

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

        # coming from a random page that is not expected
        r = test_client.post(url_for('main.unlike_recipe',
                                     recipe_url=par.recipe_tag,
                                     origin='main.about',
                                     sort_by=sort_by,
                                     search_query=search_term),
                             follow_redirects=True)
        assert route_meta_tag(r) == 'main.home'


class TestRoutesAuth:

    def test_signup(self, test_client, user, pg):

        from application.models import User

        # We are already logged in
        login(test_client, user.name, user.pw)
        r = test_client.post(url_for('auth.signup'), follow_redirects=True)
        assert route_meta_tag(r) == 'main.home'

        # We are not logged in
        logout(test_client)
        r = test_client.post(url_for('auth.signup'), follow_redirects=True)
        assert route_meta_tag(r) == 'auth.signup'

        # Username already exists
        r = test_client.post(url_for('auth.signup'), data={
            'username': user.name
            }, follow_redirects=True)
        assert b'Username already exists.' in r.data
        assert b'Please select a different username.' in r.data

        # Email already exists
        r = test_client.post(url_for('auth.signup'), data={
            'email': user.email
            }, follow_redirects=True)
        assert b'There is already an account' in r.data
        assert b'registered with this email address.' in r.data

        # Invalid username
        r = test_client.post(url_for('auth.signup'), data={
            'username': 'abc'
            }, follow_redirects=True)
        assert b'Username must' in r.data
        assert b'be between 4 and 25 characters' in r.data

        # Invalid email
        r = test_client.post(url_for('auth.signup'), data={
            'email': 'asdjkflaevzmekfj.com'
            }, follow_redirects=True)
        assert b'Please enter a valid email address' in r.data

        # Invalid password
        r = test_client.post(url_for('auth.signup'), data={
            'password': 'abc'
            }, follow_redirects=True)
        assert b'Password must be' in r.data
        assert b'between 8 and 25 characters' in r.data

        # Invalid password confirmation
        r = test_client.post(url_for('auth.signup'), data={
            'password': user.pw,
            'confirm_pswd': user.pw + 'a'
            }, follow_redirects=True)
        assert b'Passwords' in r.data
        assert b'must match' in r.data

        # Terms and conditions not ticked
        r = test_client.post(url_for('auth.signup'), data={
            'optin_terms': []
            }, follow_redirects=True)
        assert b'You have to accept the terms' in r.data
        assert b'and conditions to create an account.' in r.data

        # Valid submission
        u = User.query.filter_by(username=pg.dummy_name).first()
        if u:
            pg.delete_account(u.userID)

        r = test_client.post(url_for('auth.signup'), data={
            'email': pg.dummy_email,
            'username': pg.dummy_name,
            'password': pg.dummy_password,
            'confirm_pswd': pg.dummy_password,
            'optin_terms': True,
            'optin_news': False
            }, follow_redirects=True)
        assert b'Account registered successfully.' in r.data

        # Clean up: Delete dummy account
        u = User.query.filter_by(username=pg.dummy_name).first()
        pg.delete_account(u.userID)

    def test_signin(self, test_client, user):

        # user already signed in
        login(test_client, user.name, user.pw)
        r = test_client.get(url_for('auth.signin'), follow_redirects=True)
        assert route_meta_tag(r) == 'main.home'
        logout(test_client)

        # user not signed in
        r = test_client.get(url_for('auth.signin'), follow_redirects=True)
        assert r.status_code == 200
        assert route_meta_tag(r) == 'auth.signin'

        # Incorrect username
        r = login(test_client, user.name + 'x290fdsjkl', user.pw)
        assert b'Username or password is incorrect' in r.data

        # Incorrect password
        r = login(test_client, user.name, user.pw + 'x13fhszlfo')
        assert b'Username or password is incorrect' in r.data

    def test_logout(self, test_client, user):

        r = logout(test_client)
        assert r.status_code == 200
        assert route_meta_tag(r) == 'auth.signin'

    def test_login_logout(self, test_client, user):
        """ Test navbar changes appropriate to login status """

        # Logged in
        login(test_client, user.name, user.pw)
        r = test_client.get(url_for('main.home'), follow_redirects=True)
        assert b'Cookbook' in r.data
        assert b'Logout' in r.data
        assert b'Profile' in r.data
        assert b'Login' not in r.data
        assert b'Sign up' not in r.data

        # Logged out
        logout(test_client)
        r = test_client.get(url_for('main.home'), follow_redirects=True)
        assert b'Cookbook' not in r.data
        assert b'Logout' not in r.data
        assert b'Profile' not in r.data
        assert b'Login' in r.data
        assert b'Sign up' in r.data

    def test_terms_and_conditions(self, test_client, user):
        """ Redirects to external website with SRR's tac """

        r = test_client.get(url_for('auth.terms_and_conditions'),
                            follow_redirects=True)
        assert r.status_code == 200

    def test_reset_password_request(self, test_client, user):
        """ Receives email from user and sends password reset link """

        # if user is already logged in, we should redirect home
        login(test_client, user.name, user.pw)
        r = test_client.post(url_for('auth.reset_password_request'),
                             follow_redirects=True)
        assert r.status_code == 200
        assert route_meta_tag(r) == 'main.home'

        # when not logged in, with invalid email
        logout(test_client)
        form_data = {'email': 'not-a-valid-email.com'}
        r = test_client.post(url_for('auth.reset_password_request'),
                             follow_redirects=True, json=form_data)
        assert r.status_code == 200
        assert route_meta_tag(r) == 'auth.reset_password_request'

        # when not logged in, with valid email
        form_data = {'email': user.email}
        r = test_client.post(url_for('auth.reset_password_request'),
                             follow_redirects=True, json=form_data)
        assert r.status_code == 200
        assert route_meta_tag(r) == 'auth.signin'
        assert b'Check your email for the instructions to reset your password'\
            in r.data

    def test_reset_password(self, test_client, user):
        """
        When given a valid reset password token, resets the password
        given by user.
        """
        from application.models import User

        # if user is already logged in, we should redirect home
        login(test_client, user.name, user.pw)
        r = test_client.get(url_for('auth.reset_password',
                                    token='some_token'),
                            follow_redirects=True)
        assert r.status_code == 200
        assert route_meta_tag(r) == 'main.home'

        # when not logged in, with invalid token
        logout(test_client)
        r = test_client.get(url_for('auth.reset_password',
                                    token='bad_token'),
                            follow_redirects=True)
        assert r.status_code == 200
        assert route_meta_tag(r) == 'main.home'

        # when not logged in, with valid token
        u = User.query.filter_by(userID=user.userID).first()
        r = test_client.get(url_for('auth.reset_password',
                                    token=u.get_reset_password_token()),
                            follow_redirects=True)
        assert r.status_code == 200
        assert route_meta_tag(r) == 'auth.reset_password'

        # resetting password (invalid pwd)
        r = test_client.post(url_for('auth.reset_password',
                                     token=u.get_reset_password_token()),
                             data={'password': 'abc',
                                   'confirm_pswd': 'abc'},
                             follow_redirects=True)
        assert route_meta_tag(r) == 'auth.reset_password'
        assert b'Password must be' in r.data
        assert b'between 8 and 25 characters' in r.data

        # resetting password (empty password)
        r = test_client.post(url_for('auth.reset_password',
                                     token=u.get_reset_password_token()),
                             follow_redirects=True)
        assert route_meta_tag(r) == 'auth.reset_password'
        assert b'Password required' in r.data

        # resetting password (use the old pwd)
        u = User.query.filter_by(username=user.name).first()
        r = test_client.post(url_for('auth.reset_password',
                                     token=u.get_reset_password_token()),
                             data={'password': user.pw,
                                   'confirm_pswd': user.pw},
                             follow_redirects=True)
        assert route_meta_tag(r) == 'auth.signin'
        assert b'Your password has been reset.' in r.data

    def test_verify_email(self, test_client, user, pg):
        """
        When given a valid verify email token, updates table
        entry to user.confirmed = True
        """
        from application.models import User

        u = User.query.filter_by(userID=user.userID).first()

        # User is logged in, verification works
        login(test_client, user.name, user.pw)
        if u.confirmed:
            u.confirmed = False
            pg.session.commit()
        r = test_client.post(url_for('auth.verify_email',
                                     token=u.get_verify_email_token()),
                             follow_redirects=True)
        assert route_meta_tag(r) == 'main.profile'
        assert b'Thank you. Your email has been verified.' in r.data
        assert u.confirmed is True

        # User is not logged in, verification fails
        logout(test_client)
        if u.confirmed:
            u.confirmed = False
            pg.session.commit()
        r = test_client.post(url_for('auth.verify_email',
                                     token=u.get_verify_email_token()),
                             follow_redirects=True)
        assert route_meta_tag(r) == 'main.home'
        assert b'You need to be logged in in order to verify your email.'\
            in r.data
        assert u.confirmed is False

        # Logged in, but invalid token, verification fails
        login(test_client, user.name, user.pw)
        if u.confirmed:
            u.confirmed = False
            pg.session.commit()
        r = test_client.post(url_for('auth.verify_email',
                                     token='bad_token'),
                             follow_redirects=True)
        assert route_meta_tag(r) == 'main.profile'
        assert b'Oh oh! Email verification failed.' in r.data
        assert u.confirmed is False


# eof
