from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp, ValidationError

from app.modules.companies.repository import CompanyRepository
from app.modules.companies.validators import (
    validate_company_code,
    validate_company_name,
    validate_gst_number,
    validate_pan_number,
)


class CompanyForm(FlaskForm):
    company_id = HiddenField()
    company_name = StringField(
        'Company Name',
        filters=[lambda x: x.strip() if x else x],
        validators=[
            DataRequired(message='Enter the company name.'),
            Length(min=3, max=150, message='Company name must be between 3 and 150 characters.'),
        ],
    )
    company_code = StringField(
        'Company Code',
        filters=[lambda x: x.strip().upper() if x else x],
        validators=[
            DataRequired(message='Enter the company code.'),
            Length(min=2, max=20, message='Company code must be 2 to 20 characters.'),
            Regexp(r'^[A-Z0-9_-]+$', message='Company code may only include uppercase letters, numbers, underscore and hyphen.'),
        ],
    )
    gst_number = StringField(
        'GST Number',
        filters=[lambda x: x.strip().upper() if x else x],
        validators=[
            Optional(),
            Regexp(
                r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$',
                message='Enter a valid GST number.',
            ),
        ],
    )
    pan_number = StringField(
        'PAN Number',
        filters=[lambda x: x.strip().upper() if x else x],
        validators=[
            Optional(),
            Regexp(r'^[A-Z]{5}[0-9]{4}[A-Z]$', message='Enter a valid PAN number.'),
        ],
    )
    email = StringField(
        'Company Email',
        filters=[lambda x: x.strip().lower() if x else x],
        validators=[Optional(), Email(message='Enter a valid email address.')],
    )
    phone = StringField(
        'Phone Number',
        filters=[lambda x: x.strip() if x else x],
        validators=[Optional(), Regexp(r'^[6-9][0-9]{9}$', message='Enter a valid 10-digit Indian phone number.')],
    )
    country_id = StringField('Country', validators=[DataRequired(message='Select a country.')])
    state_id = StringField('State', validators=[DataRequired(message='Select a state.')])
    city_id = StringField('City', validators=[DataRequired(message='Select a city.')])
    pincode = StringField(
        'Pincode',
        filters=[lambda x: x.strip() if x else x],
        validators=[
            DataRequired(message='Enter the pincode.'),
            Regexp(r'^[0-9]{6}$', message='Enter a valid 6-digit pincode.'),
        ],
    )
    status = SelectField(
        'Status',
        choices=[('Active', 'Active'), ('Inactive', 'Inactive'), ('Suspended', 'Suspended')],
        default='Active',
        validators=[DataRequired(message='Select company status.')],
    )
    submit = SubmitField('Save Company')

    def __init__(self, *args, company_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_company_id = company_id
        self.company_id.data = company_id
        self.repository = CompanyRepository()

    def validate_company_name(self, field):
        if not validate_company_name(field.data):
            raise ValidationError('Company name has invalid characters.')
        if self.repository.exists_by_field('company_name', field.data, exclude_id=self.form_company_id):
            raise ValidationError('A company with that name already exists.')

    def validate_company_code(self, field):
        if not validate_company_code(field.data):
            raise ValidationError('Company code must be 2-20 characters and only contain uppercase letters, numbers, underscore, or hyphen.')
        if self.repository.exists_by_field('company_code', field.data, exclude_id=self.form_company_id):
            raise ValidationError('That company code is already in use.')

    def validate_gst_number(self, field):
        if field.data and not validate_gst_number(field.data):
            raise ValidationError('Enter a valid GST number.')
        if field.data and self.repository.exists_by_field('gst_number', field.data, exclude_id=self.form_company_id):
            raise ValidationError('That GST number is already registered.')

    def validate_pan_number(self, field):
        if field.data and not validate_pan_number(field.data):
            raise ValidationError('Enter a valid PAN number.')
        if field.data and self.repository.exists_by_field('pan_number', field.data, exclude_id=self.form_company_id):
            raise ValidationError('That PAN number is already registered.')

    def validate_email(self, field):
        if field.data and self.repository.exists_by_field('email', field.data, exclude_id=self.form_company_id):
            raise ValidationError('That email is already registered.')

    def validate_phone(self, field):
        if field.data and self.repository.exists_by_field('phone', field.data, exclude_id=self.form_company_id):
            raise ValidationError('That phone number is already registered.')
