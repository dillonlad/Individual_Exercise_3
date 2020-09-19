from flask_wtf import FlaskForm
from flask_wysiwyg.wysiwyg import WysiwygField
from wtforms import SubmitField, StringField, PasswordField, RadioField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, EqualTo, Email, Length, ValidationError

from app.models import Profile, Authors


class CommentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    comment = StringField('Comment')
    rating = RadioField('Leave a rating (5 being the best)', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')])
    post_on_page = RadioField('Are you happy for this reply to be posted on the page?', validators=[DataRequired()], choices=[('Yes','Yes'),('No','No')])
    newsletter = RadioField('Would you like to sign up for our email newsletter', choices=[('Yes', 'Yes'), ('No', 'No')], default='Yes')
    email = StringField('Please provide your email address if you want to sign up to our newsletter')
    Submit = SubmitField('Submit')


class SubmitNewsletter(FlaskForm):
    specific_message_one = StringField('Opening message: ', validators=[DataRequired()])
    specific_message_two = StringField('Closing message: ', validators=[DataRequired()])
    authenticate = StringField('Admin password: ', validators=[DataRequired()])
    Submit = SubmitField('Send Newsletter')


class Newsletter(FlaskForm):
    user_name = StringField('Name ')
    user_email = StringField('Email: ')
    Submit = SubmitField('Sign up')