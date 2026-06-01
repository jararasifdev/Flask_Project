from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, DecimalField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Length

class ExpenseCategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Category')

class ExpenseForm(FlaskForm):
    project_id = SelectField('Project', validators=[DataRequired()])
    category_id = SelectField('Category', validators=[DataRequired()])
    amount = DecimalField('Amount', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    receipt_file = FileField('Receipt', validators=[Optional(), FileAllowed(['jpg', 'png', 'pdf'], 'Images or PDFs only!')])
    submit = SubmitField('Submit Expense')

class ExpenseReviewForm(FlaskForm):
    status = SelectField('Status', choices=[('Approved', 'Approved'), ('Rejected', 'Rejected')], validators=[DataRequired()])
    submit = SubmitField('Submit Review')
