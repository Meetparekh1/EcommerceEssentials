from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, FloatField, IntegerField, SelectField, HiddenField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange
from utils.pincodes import is_valid_pincode

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class AddressForm(FlaskForm):
    address_line1 = StringField('Address Line 1', validators=[DataRequired(), Length(max=255)])
    address_line2 = StringField('Address Line 2', validators=[Optional(), Length(max=255)])
    city = StringField('City', validators=[DataRequired(), Length(max=100)])
    state = StringField('State', validators=[DataRequired(), Length(max=100)])
    pincode = StringField('PIN Code', validators=[DataRequired(), Length(min=6, max=6)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    is_default = BooleanField('Set as Default Address')
    submit = SubmitField('Save Address')
    
    def validate_pincode(self, pincode):
        if not is_valid_pincode(pincode.data):
            raise ValueError('Invalid PIN code. Please enter a valid Indian PIN code.')

class CheckoutForm(FlaskForm):
    address_id = RadioField('Select Delivery Address', coerce=int, validators=[DataRequired()])
    payment_method = SelectField('Payment Method', choices=[
        ('cod', 'Cash on Delivery'), 
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI'),
        ('netbanking', 'Net Banking')
    ], validators=[DataRequired()])
    submit = SubmitField('Proceed to Payment')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=0)])
    image_url = StringField('Image URL', validators=[DataRequired(), Length(max=200)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    featured = BooleanField('Featured Product')
    submit = SubmitField('Save Product')
