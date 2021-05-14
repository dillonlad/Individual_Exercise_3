from flask_wtf import FlaskForm
from flask_wysiwyg.wysiwyg import WysiwygField
from wtforms import SubmitField, StringField, PasswordField, RadioField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, EqualTo, Email, Length, ValidationError

from app.models import Profile, Authors



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


class OTPForm(FlaskForm):
    otp_code = StringField('OTP Code')


class CreateArticle(FlaskForm):
    Title = StringField('Title', validators=[DataRequired()])
    Post_ID = StringField('Post_ID', validators=[DataRequired()])
    Description = StringField('Description', validators=[DataRequired()])
    Image_root = StringField('Create image filename - use keywords and dashes (example-keyword-filename)', validators=[DataRequired()])
    Content = TextAreaField('Content', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    author = SelectField(u'Author', choices=[('0',''), ('Dillon Lad', 'Dillon Lad'), ('Rajan Kholia','Rajan Kholia')], validators=[DataRequired()])
    keywords = StringField('Keywords', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SearchForm(FlaskForm):
    Search = StringField('Search for articles:', id="form-search")
    Submit = SubmitField('Search', id="form-submit")


class ImageUpload(FlaskForm):
    filename = StringField("Filename")
    Submit = SubmitField('Submit', id="form-submit")


