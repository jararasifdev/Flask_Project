from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Email, Length

class CreateCompanyForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired(), Length(max=255)])
    company_email = StringField('Company Email', validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=50)])
    registration_no = StringField('Registration Number', validators=[DataRequired(), Length(max=100)])
    tax_id = StringField('Tax ID', validators=[Length(max=100)])
    address = TextAreaField('Address', validators=[DataRequired()])
    
    admin_name = StringField('Admin Full Name', validators=[DataRequired(), Length(max=255)])
    admin_email = StringField('Admin Email Address', validators=[DataRequired(), Email(), Length(max=255)])
    admin_password = PasswordField('Temporary Password', validators=[DataRequired(), Length(min=6)])
