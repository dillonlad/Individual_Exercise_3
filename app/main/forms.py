from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Email


class CommentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    comment = StringField('Comment', validators=[DataRequired()])
    date = StringField('Date')
    submit = SubmitField('Comment')