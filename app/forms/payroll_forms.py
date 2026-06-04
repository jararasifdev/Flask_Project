from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Optional

class GeneratePayrollForm(FlaskForm):
    payroll_month = DateField('Payroll Month (e.g., 2026-06-01)', validators=[DataRequired()])
    submit = SubmitField('Generate Payroll')

class EditPayrollItemForm(FlaskForm):
    base_salary = DecimalField('Base Salary', validators=[DataRequired()])
    overtime_amount = DecimalField('Overtime Amount', validators=[Optional()])
    bonus_amount = DecimalField('Bonus Amount', validators=[Optional()])
    deductions = DecimalField('Deductions', validators=[Optional()])
    submit = SubmitField('Save Item')
