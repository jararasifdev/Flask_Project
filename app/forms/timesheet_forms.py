from flask_wtf import FlaskForm
from wtforms import DateField, TimeField, DecimalField, BooleanField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional

class TimesheetForm(FlaskForm):
    project_id = SelectField('Project', validators=[DataRequired()])
    work_date = DateField('Work Date', validators=[DataRequired()])
    start_time = TimeField('Start Time', validators=[Optional()])
    end_time = TimeField('End Time', validators=[Optional()])
    total_hours = DecimalField('Total Hours', validators=[DataRequired()])
    is_billable = BooleanField('Billable to Client')
    task_description = TextAreaField('Task Description', validators=[Optional()])
    submit = SubmitField('Log Time')

class ReviewTimesheetForm(FlaskForm):
    status = SelectField('Status', choices=[('Approved', 'Approve'), ('Rejected', 'Reject')], validators=[DataRequired()])
    submit = SubmitField('Submit Review')
