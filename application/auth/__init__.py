from flask import Blueprint

bp = Blueprint('auth', __name__)

from application.auth import routes


# eof
