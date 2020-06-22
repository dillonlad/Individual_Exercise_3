from flask_wtf import FlaskForm
from flask_wysiwyg.wysiwyg import WysiwygField
from wtforms import SubmitField, StringField, PasswordField, RadioField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, EqualTo, Email, Length, ValidationError

from app.models import Profile, Authors


class CommentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    comment = StringField('Comment', validators=[DataRequired()])
    post_on_page = RadioField('Are you happy for this reply to be posted on the page?', validators=[DataRequired()], choices=[('Yes','Yes'),('No','No')])
    newsletter = RadioField('Would you like to sign up for our email newsletter', choices=[('Yes', 'Yes'), ('No', 'No')], default='No')
    email = StringField('Please provide your email address if you want to sign up to our newsletter')
    Submit = SubmitField('Comment')


class PostForm(FlaskForm):
    article_title = StringField(u'title', validators=[DataRequired(), Length(1, 64)])
    body = WysiwygField(u"txteditor", validators=[DataRequired()])
    submit = SubmitField(u'submit')


class BlogEditor(FlaskForm):
    title = StringField("title", validators=[DataRequired()])
    text = TextAreaField("text", validators=[DataRequired()])
    tags = StringField("tags", validators=[DataRequired()])
    draft = BooleanField("draft", default=False)
    submit = SubmitField("submit")


class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email address', validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                             validators=[DataRequired(), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat Password')
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = Profile.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('An account is already registered for that username.')

    def validate_email(self, email):
        user = Profile.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('An account is already registered for that email.')


class LoginForm(FlaskForm):
    email = StringField('Email address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])


class CreateArticle(FlaskForm):
    Title = StringField('Title', validators=[DataRequired()])
    Post_ID = StringField('Post_ID', validators=[DataRequired()])
    Description = StringField('Description', validators=[DataRequired()])
    Image_root = StringField('Image_root', validators=[DataRequired()])
    url_ = StringField('URL', validators=[DataRequired()])
    Content = TextAreaField('Content', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    author = SelectField(u'Author', choices=[('0',''), ('Dillon Lad', 'Dillon Lad'), ('Rajan Kholia','Rajan Kholia')], validators=[DataRequired()])
    keywords = StringField('Keywords', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SearchForm(FlaskForm):
    Search = StringField('Search for articles:')
    Submit = SubmitField('Search')


class SubmitNewsletter(FlaskForm):
    specific_message_one = StringField('Opening message: ', validators=[DataRequired()])
    specific_message_two = StringField('Closing message: ', validators=[DataRequired()])
    authenticate = StringField('Admin password: ', validators=[DataRequired()])
    Submit = SubmitField('Send Newsletter')