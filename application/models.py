from . import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __table__ = db.Model.metadata.tables['users']

    def get_id(self):
        return (self.userID)

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Recipe(db.Model):
    __table__ = db.Model.metadata.tables['recipes']

    def __repr__(self):
        return '<Post {}>'.format(self.title)


class Like(db.Model):
    __table__ = db.Model.metadata.tables['likes']

    def __repr__(self):
        return '<Post {}>'.format(self.likeID)


class ContentSimilarity(db.Model):
    __table__ = db.Model.metadata.tables['content_similarity200']

    def __repr__(self):
        return '<Post {}>'.format(self.recipeID)


class ContentSimilarityID(db.Model):
    __table__ = db.Model.metadata.tables['content_similarity200_ids']

    def __repr__(self):
        return '<Post {}>'.format(self.recipeID)

# eof
