from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class LoginForm(FlaskForm):
    login_identifier = StringField(
        'Email or Username',
        validators=[DataRequired(message='Enter your email or username.')],
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(message='Enter your password.')],
    )
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign in securely')


class ForgotPasswordForm(FlaskForm):
    email = StringField(
        'Email address',
        validators=[DataRequired(message='Enter your email address.'), Email(message='Enter a valid email address.')],
    )
    submit = SubmitField('Send reset link')


class ResetPasswordForm(FlaskForm):
    token = StringField('Token', validators=[DataRequired()])
    new_password = PasswordField(
        'New password',
        validators=[
            DataRequired(message='Enter a new password.'),
            Length(min=12, message='Password must be at least 12 characters.'),
            EqualTo('confirm_password', message='Passwords must match.'),
        ],
    )
    confirm_password = PasswordField('Confirm password', validators=[DataRequired(message='Confirm your password.')])
    submit = SubmitField('Reset password')
