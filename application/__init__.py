""" Flask application factory """
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from csp import csp
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from config import DevConfig, ProdConfig
from flask_mail import Mail


# Database
db = SQLAlchemy()

# Security
csrf = CSRFProtect()
talisman = Talisman()

# Login Manager
login = LoginManager()
login.login_view = 'auth.signin'

# Mail
mail = Mail()


def create_app(testing=True, debug=True):
    """ App factory """

    # Initialize application
    app = Flask(__name__)
    if testing | debug:
        app.config.from_object(DevConfig)
    else:
        app.config.from_object(ProdConfig)
    app.debug = debug

    # Initialize extensions
    csrf.init_app(app)
    db.init_app(app)
    if testing | debug:
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
    mail.init_app(app)

    with app.app_context():

        # Create models from existing DB
        db.Model.metadata.reflect(db.engine)

        # Create Routes
        from application.main import bp as main_bp
        app.register_blueprint(main_bp)

        from application.auth import bp as auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')

        return app


# eof
