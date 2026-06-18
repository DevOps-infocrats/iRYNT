from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp, ValidationError

from app.modules.clients.repository import ClientRepository
from app.modules.clients.validators import validate_client_code, validate_client_name, validate_client_phone
from app.modules.circles.models import Circle
from app.modules.companies.models import Company


class ClientForm(FlaskForm):
    company_id = SelectField('Company', choices=[], validators=[DataRequired(message='Select a company.')])
    circle_id = SelectField('Circle', choices=[], validators=[DataRequired(message='Select a circle.')])
    client_id = HiddenField()
    client_code = StringField(
        'Client Code',
        filters=[lambda x: x.strip().upper() if x else x],
        validators=[
            DataRequired(message='Enter the client code.'),
            Length(min=2, max=20, message='Client code must be 2 to 20 characters.'),
            Regexp(r'^[A-Z0-9_-]+$', message='Client code may only include uppercase letters, numbers, underscore and hyphen.'),
        ],
    )
    client_name = StringField(
        'Client Name',
        filters=[lambda x: x.strip() if x else x],
        validators=[
            DataRequired(message='Enter the client name.'),
            Length(min=3, max=150, message='Client name must be 3 to 150 characters.'),
        ],
    )
    primary_contact = StringField('Primary Contact', validators=[Optional(), Length(max=150)])
    email = StringField('Contact Email', validators=[Optional(), Email(message='Enter a valid email address.')])
    phone = StringField('Contact Phone', validators=[Optional(), Length(max=15)])
    address = TextAreaField('Client Address', validators=[Optional(), Length(max=1000)])
    status = SelectField(
        'Status',
        choices=[('Active', 'Active'), ('Inactive', 'Inactive')],
        default='Active',
        validators=[DataRequired(message='Select client status.')],
    )
    submit = SubmitField('Save Client')

    def __init__(self, *args, companies=None, circles=None, company_id=None, circle_id=None, client_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_company_id = company_id
        self.form_client_id = client_id
        self.company_id.choices = [('', 'Select company')] + [
            (company.id, f"{company.company_name} ({company.company_code})") for company in (companies or [])
        ]
        self.circle_id.choices = [('', 'Select circle')] + [
            (circle.id, f"{circle.circle_name} ({circle.circle_code})") for circle in (circles or [])
        ]
        if company_id is not None:
            self.company_id.data = company_id
        if circle_id is not None:
            self.circle_id.data = circle_id
        if client_id is not None:
            self.client_id.data = client_id
        self.repository = ClientRepository()

    def validate_company_id(self, field):
        if not field.data:
            raise ValidationError('Select a valid company.')
        if not Company.query.get(field.data):
            raise ValidationError('Select a valid company.')

    def validate_circle_id(self, field):
        if not field.data:
            raise ValidationError('Select a valid circle.')
        circle = Circle.query.get(field.data)
        if not circle:
            raise ValidationError('Select a valid circle.')
        company_id = self.company_id.data or self.form_company_id
        if circle.company_id != company_id:
            raise ValidationError('Selected circle does not belong to the selected company.')

    def validate_client_code(self, field):
        if not validate_client_code(field.data):
            raise ValidationError('Client code must be 2-20 uppercase letters, numbers, underscore or hyphen.')
        company_id = self.company_id.data or self.form_company_id
        if self.repository.exists_by_field('client_code', field.data, company_id=company_id, exclude_id=self.form_client_id):
            raise ValidationError('That client code is already in use for the selected company.')

    def validate_client_name(self, field):
        if not validate_client_name(field.data):
            raise ValidationError('Client name must contain only letters, numbers and basic punctuation.')

    def validate_phone(self, field):
        if field.data and not validate_client_phone(field.data):
            raise ValidationError('Enter a valid 10-digit Indian phone number.')

    def validate_email(self, field):
        if field.data:
            company_id = self.company_id.data or self.form_company_id
            if self.repository.exists_by_field('email', field.data, company_id=company_id, exclude_id=self.form_client_id):
                raise ValidationError('That email is already in use for the selected company.')
