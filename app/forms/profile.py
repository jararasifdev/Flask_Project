from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo

class UpdateProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Phone Number', validators=[Length(max=50)])
    password = PasswordField('New Password (leave blank to keep current)', validators=[])
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('password')])
    submit = SubmitField('Update Profile')
