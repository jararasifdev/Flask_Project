from flask_wtf import FlaskForm
from wtforms import StringField, DateField, DecimalField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional

class InvoiceForm(FlaskForm):
    client_id = SelectField('Client', validators=[DataRequired()])
    project_id = SelectField('Project (Optional)', validators=[Optional()])
    invoice_number = StringField('Invoice Number', validators=[DataRequired()])
    issue_date = DateField('Issue Date', validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('Draft', 'Draft'), ('Sent', 'Sent'), ('Partial', 'Partial'), 
        ('Paid', 'Paid'), ('Overdue', 'Overdue')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Invoice')

class InvoiceItemForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    quantity = DecimalField('Quantity', validators=[DataRequired()])
    rate = DecimalField('Rate/Price', validators=[DataRequired()])
    submit = SubmitField('Add Item')

class PaymentForm(FlaskForm):
    payment_date = DateField('Payment Date', validators=[DataRequired()])
    amount_paid = DecimalField('Amount Paid', validators=[DataRequired()])
    payment_method = StringField('Payment Method', validators=[Optional()])
    reference_number = StringField('Reference Number', validators=[Optional()])
    submit = SubmitField('Record Payment')

class InvoiceStatusForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('Draft', 'Draft'), ('Sent', 'Sent'), ('Partial', 'Partial'), 
        ('Paid', 'Paid'), ('Overdue', 'Overdue')
    ], validators=[DataRequired()])
    submit = SubmitField('Update Status')
