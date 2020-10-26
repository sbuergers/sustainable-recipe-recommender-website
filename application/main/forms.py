""" main application forms """
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


class SearchForm(FlaskForm):
    search = StringField('search')
    submit = SubmitField('Search',
                         render_kw={'class': 'btn btn-success btn-block'})


# eof
