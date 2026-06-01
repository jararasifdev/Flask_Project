from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Length, ValidationError
from app.models.client import Client
from flask_login import current_user

class ClientForm(FlaskForm):
    client_name = StringField('Client Name', validators=[DataRequired(), Length(max=255)])
    company_name = StringField('Company Name', validators=[Optional(), Length(max=255)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=255)])
    phone = StringField('Phone', validators=[Optional(), Length(max=50)])
    address = TextAreaField('Address', validators=[Optional()])
    submit = SubmitField('Save Client')

    def validate_email(self, email):
        if email.data:
            client = Client.query.filter_by(email=email.data, company_id=current_user.company_id).first()
            if client:
                raise ValidationError('A client with this email already exists.')
