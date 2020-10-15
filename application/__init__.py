""" Flask application factory """
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from csp import csp
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from config import DevConfig


# Database
db = SQLAlchemy()

# Security
csrf = CSRFProtect()
talisman = Talisman()

# Login Manager
login = LoginManager()
login.login_view = 'signin'


def create_app(cfg=DevConfig):
    """ App factory """

    # Initialize application
    app = Flask(__name__)
    app.config.from_object(cfg)
    app.debug = app.config['DEBUG']  # remove?

    # Initialize extensions
    csrf.init_app(app)
    db.init_app(app)
    if app.config['TESTING'] | app.config['DEBUG']:
        talisman.init_app(
            app,
            content_security_policy=csp,
            content_security_policy_nonce_in=['script-src'],
            force_https=False
        )
    else:
        talisman.init_app(
            app,
            content_security_policy=csp,
            content_security_policy_nonce_in=['script-src'],
            force_https=True
        )
    login.init_app(app)

    # Load routes and models in application
    with app.app_context():

        from application import routes

        db.Model.metadata.reflect(db.engine)
        from application import models

        return app


# eof
