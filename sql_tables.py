from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """ User model """

    __tablename__ = "users"
    userID = db.Column(
        db.Integer,
        primary_key=True
    )
    username = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )
    password = db.Column(
        db.String(),
        nullable=False
    )
    created = db.Column(
        db.DateTime,
        index=False,
        unique=False,
        nullable=False
    )
    email = db.Column(
        db.String(80),
        index=True,
        unique=True,
        nullable=False
    )

    def get_id(self):
        return (self.userID)

    def __repr__(self):
        return '<User {0}>'.format(self.username)


# eof
