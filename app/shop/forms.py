from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField, RadioField, BooleanField, TextAreaField, SelectField, \
    IntegerField
from wtforms.validators import DataRequired, EqualTo, Email, Length, ValidationError, AnyOf, NoneOf


def validating_input(form, field):
    if 'Please' in field.data:
        return ValidationError("Please select a colour")


class testShop(FlaskForm):
    colour = SelectField('Colour: ', choices=[('Please select', 'Please select'), ('White', 'White'), ('Grey', 'Grey')], validators=[NoneOf(values=['Please select'], message="Please select a colour")])
    size = SelectField('Size: ', choices=[('Please select', 'Please select'), ('XS', 'XS - Not available'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL - Not available')], validators=[NoneOf(values=['Please select'], message="Please select a colour")])
    quantity = SelectField('Quantity: ', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')])
    submit = SubmitField('ADD TO CART')



class EnquiryForm(FlaskForm):
    name = StringField('Name: ', validators=[DataRequired()])
    email = StringField('Email address: ', validators=[DataRequired(), Email()])
    message = TextAreaField('Message: ', validators=[DataRequired()])
    submit = SubmitField('Send')


class RatingForm(FlaskForm):
    name = StringField('Name: ')
    stars = RadioField('Leave a rating (5 being the best)', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')])
    comment = TextAreaField('Comments: ')
    submit = SubmitField('Submit')


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
