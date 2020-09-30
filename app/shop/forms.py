from flask_wtf import FlaskForm
from flask_wysiwyg.wysiwyg import WysiwygField
from wtforms import SubmitField, StringField, PasswordField, RadioField, BooleanField, TextAreaField, SelectField, \
    IntegerField
from wtforms.validators import DataRequired, EqualTo, Email, Length, ValidationError


class testShop(FlaskForm):
    size = SelectField('Size: ', choices=[('XS - Not available', 'XS - Not available'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL - Not available', 'XL - Not available')])
    colour = SelectField('Colour: ', choices=[('White', 'White'), ('Black', 'Black')])
    quantity = SelectField('Quantity: ', choices=[('1','1'),('2','2'),('3','3'),('4','4'),('5','5')])
    submit = SubmitField('Add to cart')


class EnquiryForm(FlaskForm):
    name = StringField('Name: ', validators=[DataRequired()])
    email = StringField('Email address: ', validators=[DataRequired(), Email()])
    message = TextAreaField('Message: ', validators=[DataRequired()])
    submit = SubmitField('Send')


class CreditCardPayment(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    line1 = StringField('Address', validators=[DataRequired()])
    city = StringField('City: ', validators=[DataRequired()])
    state = StringField('State: ')
    postal_code = StringField('City: ', validators=[DataRequired()])
    country_code = StringField('Country: ', validators=[DataRequired()])
    type = SelectField('Type', validators=[DataRequired()], choices=[('Mastercard', 'mastercard')])
    number = StringField('Card Number: ', validators=[DataRequired()])
    expire_month = StringField('Month', validators=[DataRequired()])
    expire_year = StringField('Year', validators=[DataRequired()])
    cvv2 = StringField('CVS: ', validators=[DataRequired()])
    submit = SubmitField('Next')
