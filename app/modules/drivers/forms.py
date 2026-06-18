from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import DateField, IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from app.modules.vehicles.validators import validate_phone

ALLOWED_DRIVER_DOCUMENT_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg']

GENDER_CHOICES = [
    ('', 'Select gender'),
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
]

BLOOD_GROUP_CHOICES = [
    ('', 'Select blood group'),
    ('A+', 'A+'),
    ('A-', 'A-'),
    ('B+', 'B+'),
    ('B-', 'B-'),
    ('AB+', 'AB+'),
    ('AB-', 'AB-'),
    ('O+', 'O+'),
    ('O-', 'O-'),
]

DOCUMENT_TYPE_CHOICES = [
    ('', 'Select document type'),
    ('Driving License', 'Driving License'),
    ('Address Proof', 'Address Proof'),
    ('Photo ID', 'Photo ID'),
    ('Medical Certificate', 'Medical Certificate'),
]


class DriverCreateForm(FlaskForm):
    identifier = StringField(
        'User (Email or Username)',
        validators=[DataRequired(message='Please enter a user email or username.'), Length(max=120)],
        render_kw={'class': 'form-control', 'placeholder': 'user@example.com or username'},
    )

    phone = StringField(
        'Phone Number',
        validators=[Optional(), validate_phone],
        render_kw={'class': 'form-control', 'placeholder': '10-digit mobile number'},
    )

    driver_code = StringField(
        'Driver Code',
        validators=[Optional(), Length(max=50)],
        render_kw={'class': 'form-control', 'placeholder': 'DR-001'},
    )

    company_id = SelectField(
        'Company',
        choices=[('', 'Select company')],
        validators=[Optional()],
        render_kw={'class': 'form-select select2'},
    )

    circle_id = SelectField(
        'Circle',
        choices=[('', 'Select circle')],
        validators=[Optional()],
        render_kw={'class': 'form-select select2'},
    )

    client_id = SelectField(
        'Client',
        choices=[('', 'Select client')],
        validators=[Optional()],
        render_kw={'class': 'form-select select2'},
    )

    project_id = SelectField(
        'Project',
        choices=[('', 'Select project')],
        validators=[Optional()],
        render_kw={'class': 'form-select select2'},
    )

    subzone_id = SelectField(
        'Subzone',
        choices=[('', 'Select subzone')],
        validators=[Optional()],
        render_kw={'class': 'form-select select2'},
    )

    dob = DateField(
        'Date of Birth',
        format='%Y-%m-%d',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'YYYY-MM-DD'},
    )

    gender = SelectField(
        'Gender',
        choices=GENDER_CHOICES,
        validators=[Optional()],
        render_kw={'class': 'form-select'},
    )

    blood_group = SelectField(
        'Blood Group',
        choices=BLOOD_GROUP_CHOICES,
        validators=[Optional()],
        render_kw={'class': 'form-select'},
    )

    nationality = StringField(
        'Nationality',
        validators=[Optional(), Length(max=60)],
        default='Indian',
        render_kw={'class': 'form-control', 'placeholder': 'Indian'},
    )

    address = StringField(
        'Address',
        validators=[Optional(), Length(max=255)],
        render_kw={'class': 'form-control', 'placeholder': 'Address'},
    )

    emergency_contact_name = StringField(
        'Emergency Contact Name',
        validators=[Optional(), Length(max=120)],
        render_kw={'class': 'form-control', 'placeholder': 'Contact person'},
    )

    emergency_contact_phone = StringField(
        'Emergency Contact Phone',
        validators=[Optional(), validate_phone],
        render_kw={'class': 'form-control', 'placeholder': '10-digit mobile number'},
    )

    experience_years = IntegerField(
        'Experience (years)',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': '0', 'min': '0', 'type': 'number'},
    )

    join_date = DateField(
        'Join Date',
        format='%Y-%m-%d',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'YYYY-MM-DD'},
    )

    license_number = StringField(
        'License Number',
        validators=[Optional(), Length(max=80)],
        render_kw={'class': 'form-control', 'placeholder': 'DL1234567890'},
    )

    vehicle_classes = StringField(
        'Vehicle Classes',
        validators=[Optional(), Length(max=120)],
        render_kw={'class': 'form-control', 'placeholder': 'Appendix C, HMV, LMV'},
    )

    issue_date = DateField(
        'Issue Date',
        format='%Y-%m-%d',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'YYYY-MM-DD'},
    )

    expiry_date = DateField(
        'Expiry Date',
        format='%Y-%m-%d',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'YYYY-MM-DD'},
    )

    document_type = SelectField(
        'Primary Document Type',
        choices=DOCUMENT_TYPE_CHOICES,
        validators=[Optional()],
        render_kw={'class': 'form-select'},
    )

    document_file = FileField(
        'Upload Document',
        validators=[Optional(), FileAllowed(ALLOWED_DRIVER_DOCUMENT_EXTENSIONS, 'Only PDF, JPG, JPEG, and PNG files are allowed.')],
        render_kw={'class': 'form-control'},
    )

    driving_license_file = FileField(
        'Driving License',
        validators=[FileAllowed(ALLOWED_DRIVER_DOCUMENT_EXTENSIONS, 'Only PDF, JPG, JPEG, and PNG files are allowed.')],
        render_kw={'class': 'form-control'},
    )

    aadhaar_file = FileField(
        'Aadhaar Card',
        validators=[FileAllowed(ALLOWED_DRIVER_DOCUMENT_EXTENSIONS, 'Only PDF, JPG, JPEG, and PNG files are allowed.')],
        render_kw={'class': 'form-control'},
    )

    pan_file = FileField(
        'PAN Card',
        validators=[FileAllowed(ALLOWED_DRIVER_DOCUMENT_EXTENSIONS, 'Only PDF, JPG, JPEG, and PNG files are allowed.')],
        render_kw={'class': 'form-control'},
    )

    medical_certificate_file = FileField(
        'Medical Certificate',
        validators=[FileAllowed(ALLOWED_DRIVER_DOCUMENT_EXTENSIONS, 'Only PDF, JPG, JPEG, and PNG files are allowed.')],
        render_kw={'class': 'form-control', 'disabled': 'disabled'},
    )

    police_verification_file = FileField(
        'Police Verification',
        validators=[FileAllowed(ALLOWED_DRIVER_DOCUMENT_EXTENSIONS, 'Only PDF, JPG, JPEG, and PNG files are allowed.')],
        render_kw={'class': 'form-control', 'disabled': 'disabled'},
    )

    training_certificate_file = FileField(
        'Training Certificate',
        validators=[FileAllowed(ALLOWED_DRIVER_DOCUMENT_EXTENSIONS, 'Only PDF, JPG, JPEG, and PNG files are allowed.')],
        render_kw={'class': 'form-control', 'disabled': 'disabled'},
    )

    submit = SubmitField('Create Driver Profile', render_kw={'class': 'btn btn-gradient'})

    def validate_driving_license_file(self, field):
        if not field.data or not field.data.filename:
            raise ValidationError('Driving License document is mandatory.')

    def validate_aadhaar_file(self, field):
        if not field.data or not field.data.filename:
            raise ValidationError('Aadhaar document is mandatory.')

    def validate_pan_file(self, field):
        if not field.data or not field.data.filename:
            raise ValidationError('PAN document is mandatory.')


class DriverEditForm(FlaskForm):
    """Form for editing existing driver profile"""
    driver_code = StringField(
        'Driver Code',
        validators=[Optional(), Length(max=50)],
        render_kw={'class': 'form-control', 'placeholder': 'DR-001'},
    )

    circle_id = SelectField(
        'Circle',
        choices=[('', 'Select circle')],
        validators=[Optional()],
        render_kw={'class': 'form-select select2'},
    )

    client_id = SelectField(
        'Client',
        choices=[('', 'Select client')],
        validators=[Optional()],
        render_kw={'class': 'form-select select2'},
    )

    project_id = SelectField(
        'Project',
        choices=[('', 'Select project')],
        validators=[Optional()],
        render_kw={'class': 'form-select select2'},
    )

    subzone_id = SelectField(
        'Subzone',
        choices=[('', 'Select subzone')],
        validators=[Optional()],
        render_kw={'class': 'form-select select2'},
    )

    dob = DateField(
        'Date of Birth',
        format='%Y-%m-%d',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'YYYY-MM-DD'},
    )

    gender = SelectField(
        'Gender',
        choices=GENDER_CHOICES,
        validators=[Optional()],
        render_kw={'class': 'form-select'},
    )

    blood_group = SelectField(
        'Blood Group',
        choices=BLOOD_GROUP_CHOICES,
        validators=[Optional()],
        render_kw={'class': 'form-select'},
    )

    nationality = StringField(
        'Nationality',
        validators=[Optional(), Length(max=60)],
        default='Indian',
        render_kw={'class': 'form-control', 'placeholder': 'Indian'},
    )

    address = StringField(
        'Address',
        validators=[Optional(), Length(max=255)],
        render_kw={'class': 'form-control', 'placeholder': 'Address'},
    )

    emergency_contact_name = StringField(
        'Emergency Contact Name',
        validators=[Optional(), Length(max=120)],
        render_kw={'class': 'form-control', 'placeholder': 'Contact person'},
    )

    emergency_contact_phone = StringField(
        'Emergency Contact Phone',
        validators=[Optional(), validate_phone],
        render_kw={'class': 'form-control', 'placeholder': '10-digit mobile number'},
    )

    experience_years = IntegerField(
        'Experience (years)',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': '0', 'min': '0', 'type': 'number'},
    )

    join_date = DateField(
        'Join Date',
        format='%Y-%m-%d',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'YYYY-MM-DD'},
    )

    license_number = StringField(
        'License Number',
        validators=[Optional(), Length(max=80)],
        render_kw={'class': 'form-control', 'placeholder': 'DL1234567890'},
    )

    vehicle_classes = StringField(
        'Vehicle Classes',
        validators=[Optional(), Length(max=120)],
        render_kw={'class': 'form-control', 'placeholder': 'Appendix C, HMV, LMV'},
    )

    issue_date = DateField(
        'Issue Date',
        format='%Y-%m-%d',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'YYYY-MM-DD'},
    )

    expiry_date = DateField(
        'Expiry Date',
        format='%Y-%m-%d',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'YYYY-MM-DD'},
    )

    document_type = SelectField(
        'Primary Document Type',
        choices=DOCUMENT_TYPE_CHOICES,
        validators=[Optional()],
        render_kw={'class': 'form-select'},
    )

    document_file = FileField(
        'Upload Document',
        validators=[Optional(), FileAllowed(ALLOWED_DRIVER_DOCUMENT_EXTENSIONS, 'Only PDF, JPG, JPEG, and PNG files are allowed.')],
        render_kw={'class': 'form-control'},
    )

    submit = SubmitField('Update Driver Profile', render_kw={'class': 'btn btn-gradient'})
