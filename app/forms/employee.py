from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, DecimalField
from wtforms.validators import DataRequired, Email, Length, Optional

class AddEmployeeForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Initial Password', validators=[DataRequired(), Length(min=6)])
    role_id = SelectField('Role', validators=[DataRequired()])
    department_id = SelectField('Department', validators=[Optional()])
    phone = StringField('Phone Number', validators=[Length(max=50)])
    employment_type = SelectField('Employment Type', choices=[
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Contractor', 'Contractor')
    ], validators=[Optional()])
    joining_date = DateField('Joining Date', format='%Y-%m-%d', validators=[Optional()])
    monthly_salary = DecimalField('Monthly Salary', places=2, validators=[Optional()])
    submit = SubmitField('Create Employee Account')

class EditEmployeeForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    role_id = SelectField('Role', validators=[DataRequired()])
    department_id = SelectField('Department', validators=[Optional()])
    phone = StringField('Phone Number', validators=[Length(max=50)])
    employment_type = SelectField('Employment Type', choices=[
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Contractor', 'Contractor')
    ], validators=[Optional()])
    joining_date = DateField('Joining Date', format='%Y-%m-%d', validators=[Optional()])
    monthly_salary = DecimalField('Monthly Salary', places=2, validators=[Optional()])
    submit = SubmitField('Update Employee Profile')
