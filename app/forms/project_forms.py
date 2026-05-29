from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Length

class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired(), Length(max=255)])
    description = TextAreaField('Description', validators=[Optional()])
    client_id = SelectField('Client', validators=[DataRequired()])
    project_manager_id = SelectField('Project Manager', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('Not Started', 'Not Started'),
        ('In Progress', 'In Progress'),
        ('On Hold', 'On Hold'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled')
    ], validators=[DataRequired()])
    budget = DecimalField('Budget', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[Optional()])
    estimated_end_date = DateField('Estimated End Date', validators=[Optional()])
    actual_end_date = DateField('Actual End Date', validators=[Optional()])
    submit = SubmitField('Save Project')

class AssignEmployeeForm(FlaskForm):
    employee_id = SelectField('Employee', validators=[DataRequired()])
    submit = SubmitField('Assign Employee')
