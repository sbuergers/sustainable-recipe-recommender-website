""" SQLAlchemy table abstractions """
from application import db, login
from flask_login import UserMixin
from flask import current_app
from time import time
import jwt


class User(UserMixin, db.Model):
    __table__ = db.Model.metadata.tables["users"]
    likes = db.relationship("Like", backref="user", lazy="dynamic")

    def get_id(self):
        return self.userID

    def __repr__(self):
        return "<User {}>".format(self.username)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.get_id(), "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )["reset_password"]
        except:
            return
        return User.query.get(id)

    def get_verify_email_token(self, expires_in=600):
        return jwt.encode(
            {"verify_email": self.email, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

    @staticmethod
    def verify_verify_email_token(token):
        try:
            email = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )["verify_email"]
        except:
            return
        return User.query.filter_by(email=email).first()


@login.user_loader
def load_user(userID):
    return User.query.get(int(userID))


class Recipe(db.Model):
    __table__ = db.Model.metadata.tables["recipes"]

    def __repr__(self):
        return "<Recipe {}>".format(self.title)


class Like(db.Model):
    __table__ = db.Model.metadata.tables["likes"]

    def __repr__(self):
        return "<Like {}>".format(self.likeID)


class Consent(db.Model):
    __table__ = db.Model.metadata.tables["consent"]

    def __repr__(self):
        return "<Consent {}>".format(self.consentID)


class ContentSimilarity(db.Model):
    __table__ = db.Model.metadata.tables["content_similarity200"]

    def __repr__(self):
        return "<ContentSimilarity {}>".format(self.recipeID)


class ContentSimilarityID(db.Model):
    __table__ = db.Model.metadata.tables["content_similarity200_ids"]

    def __repr__(self):
        return "<ContentSimilarityID {}>".format(self.recipeID)


# eof
