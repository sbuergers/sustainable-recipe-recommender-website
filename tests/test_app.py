"""
Test script for flask application

Useful links:
https://flask.palletsprojects.com/en/1.1.x/testing/
https://pythonhosted.org/Flask-Testing/
https://www.patricksoftwareblog.com/testing-a-flask-application-using-pytest/
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


@pytest.fixture
def client():
    app = create_app(testing=True, debug=False)
    testing_client = app.test_client()
    ctx = app.app_context()
    ctx.push()
    yield testing_client  # this is where the testing happens!
    ctx.pop()


def test_home(client):
    res = client.get('/')
    assert res.status_code == 200
    res = client.get('/home')
    assert res.status_code == 200

# eof
