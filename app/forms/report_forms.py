from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, SubmitField
from wtforms.validators import DataRequired

class GenerateReportForm(FlaskForm):
    report_type = SelectField('Report Type', choices=[
        ('profit_loss', 'Profit and Loss'),
        ('budget_vs_actual', 'Project Budget vs. Actual'),
        ('employee_costs', 'Employee Costs')
    ], validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    submit = SubmitField('Generate Report')
