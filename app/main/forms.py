from flask_wtf import FlaskForm
from flask_wysiwyg.wysiwyg import WysiwygField
from wtforms import SubmitField, StringField, PasswordField, RadioField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Email, Length, ValidationError

from app.models import Profile


class CommentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    comment = StringField('Comment', validators=[DataRequired()])
    date = StringField('Date')
    submit = SubmitField('Comment')


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
    Time = StringField('Time', validators=[DataRequired()])
    Date = StringField('Date', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    author = StringField('Author', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SearchForm(FlaskForm):
    Search = StringField('Search for articles: ')
    Submit = SubmitField('Search')