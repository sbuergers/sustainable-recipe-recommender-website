"""Flask config."""
from os import environ
from dotenv import load_dotenv


load_dotenv('.env')


class Config:
    """Base config"""
    SECRET_KEY = environ.get('SECRET')
    WTF_CSRF_SECRET_KEY = environ.get('SECRET')
    SALT_EMAIL = environ.get('SALT_EMAIL')
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'

    # Database
    DATABASE_URI = environ.get('DATABASE_URL')
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_recycle': 280,
                                 'pool_timeout': 100,
                                 'pool_pre_ping': True}

    # Email (TSL errors out)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465  # for TSL use 587, for ssl use 465
    MAIL_USE_TSL = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = environ.get('MAIL_PASSWORD')
    MAIL_SUPPRESS_SEND = False
    ADMINS = ['sustainable.recipe.recommender@gmail.com']


class ProdConfig(Config):
    """Production config"""
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    WTF_CSRF_ENABLED = True


class DevConfig(Config):
    """Development config"""
    FLASK_ENV = 'development'
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False


# eof
