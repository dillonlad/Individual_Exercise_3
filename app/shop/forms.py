from flask_wtf import FlaskForm
from flask_wysiwyg.wysiwyg import WysiwygField
from wtforms import SubmitField, StringField, PasswordField, RadioField, BooleanField, TextAreaField, SelectField, \
    IntegerField
from wtforms.validators import DataRequired, EqualTo, Email, Length, ValidationError


class testShop(FlaskForm):
    size = SelectField('Size: ', choices=[('XS', 'XS'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL')])
    colour = SelectField('Colour: ', choices=[('White', 'White'), ('Black', 'Black')])
    quantity = SelectField('Quantity: ', choices=[('1','1'),('2','2'),('3','3'),('4','4'),('5','5')])
    submit = SubmitField('Add to cart')