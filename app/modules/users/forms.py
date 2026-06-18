from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError


class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[Optional(), Length(max=24)])
    password = PasswordField('Password', validators=[Optional(), Length(min=8, max=128)])
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password', message='Passwords must match'), Optional()])
    company_id = SelectField('Company', choices=[], validators=[DataRequired()])
    circle_id = SelectField('Circle', choices=[], validators=[Optional()])
    role_id = SelectField('Primary Role', choices=[], validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)
    is_verified = BooleanField('Verified', default=True)
    submit = SubmitField('Save User')

    def validate_username(self, field):
        from app.modules.auth.models import User
        user = User.query.filter_by(username=field.data).first()
        if user:
            if not getattr(self, '_obj', None) or self._obj.id != user.id:
                raise ValidationError('Username already exists.')

    def validate_email(self, field):
        from app.modules.auth.models import User
        user = User.query.filter_by(email=field.data).first()
        if user:
            if not getattr(self, '_obj', None) or self._obj.id != user.id:
                raise ValidationError('Email already exists.')

    def validate_phone(self, field):
        if field.data:
            from app.modules.auth.models import User
            user = User.query.filter_by(phone=field.data).first()
            if user:
                if not getattr(self, '_obj', None) or self._obj.id != user.id:
                    raise ValidationError('Phone number already exists.')
