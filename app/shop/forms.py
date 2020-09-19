from flask_wtf import FlaskForm
from flask_wysiwyg.wysiwyg import WysiwygField
from wtforms import SubmitField, StringField, PasswordField, RadioField, BooleanField, TextAreaField, SelectField, \
    IntegerField
from wtforms.validators import DataRequired, EqualTo, Email, Length, ValidationError


class testShop(FlaskForm):
    size = StringField('Size: ')
    colour = StringField('Colour: ')
    quantity = StringField('Quantity: ')
    submit = SubmitField('Submit')