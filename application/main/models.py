from application import db, login
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __table__ = db.Model.metadata.tables['users']

    def get_id(self):
        return (self.userID)

    def __repr__(self):
        return '<User {}>'.format(self.username)


@login.user_loader
def load_user(userID):
    return User.query.get(int(userID))


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
