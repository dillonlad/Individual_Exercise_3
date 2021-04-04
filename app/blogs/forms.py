from flask_wtf import FlaskForm
from flask_wysiwyg.wysiwyg import WysiwygField
from wtforms import SubmitField, StringField, PasswordField, RadioField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, EqualTo, Email, Length, ValidationError

from app.models import Profile, Authors


class CommentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    comment = TextAreaField('Comment')
    rating = RadioField('Leave a rating (5 being the best)', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')])
    Submit = SubmitField('Submit')


class SubmitNewsletter(FlaskForm):
    specific_message_one = TextAreaField('Opening message: ', validators=[DataRequired()])
    specific_message_two = TextAreaField('Closing message: ', validators=[DataRequired()])
    authenticate = StringField('Admin password: ', validators=[DataRequired()])
    Submit = SubmitField('Send Newsletter')


class Newsletter(FlaskForm):
    user_email = StringField('Email: ')
    Submit = SubmitField('Sign up')