from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
    DateField,
    BooleanField,
    IntegerField,
    TextAreaField,
    SubmitField,
)
from wtforms.validators import DataRequired, Optional, Length, ValidationError, Regexp
from datetime import date, datetime

from app.modules.projects.validators import (
    validate_project_code,
    validate_project_code_unique,
    validate_project_name,
    validate_project_hierarchy,
    validate_project_dates,
    validate_project_type,
    validate_project_status,
    validate_contact_number,
    validate_email,
    validate_pincode,
    validate_integer_positive,
)


class ProjectForm(FlaskForm):
    """Project Create/Edit Form with enterprise hierarchy and operational config"""

    # Hierarchy Selection
    company_id = SelectField(
        'Company',
        choices=[],
        validators=[DataRequired(message='Company is required.')],
        render_kw={'class': 'form-select'}
    )

    circle_id = SelectField(
        'Circle',
        choices=[],
        validators=[DataRequired(message='Circle is required.')],
        render_kw={'class': 'form-select'}
    )

    client_id = SelectField(
        'Client',
        choices=[],
        validators=[DataRequired(message='Client is required.')],
        render_kw={'class': 'form-select'}
    )

    # Basic Information
    project_code = StringField(
        'Project Code',
        validators=[
            DataRequired(message='Project code is required.'),
            Length(min=2, max=20, message='Project code must be 2-20 characters.'),
            Regexp(
                r'^[A-Z0-9_-]+$',
                flags=0,
                message='Use A-Z, 0-9, underscore (_), or hyphen (-) only.'
            ),
        ],
        render_kw={'class': 'form-control', 'placeholder': 'e.g., AMZ_LKO_01'}
    )

    project_name = StringField(
        'Project Name',
        validators=[
            DataRequired(message='Project name is required.'),
            Length(min=3, max=150, message='Project name must be 3-150 characters.'),
        ],
        render_kw={'class': 'form-control', 'placeholder': 'e.g., Amazon Last Mile Delivery'}
    )

    project_type = SelectField(
        'Project Type',
        choices=[
            ('', 'Select project type'),
            ('Logistics', 'Logistics'),
            ('Transportation', 'Transportation'),
            ('Delivery', 'Delivery'),
            ('Fleet Operations', 'Fleet Operations'),
            ('Warehouse Operations', 'Warehouse Operations'),
            ('Field Operations', 'Field Operations'),
        ],
        validators=[DataRequired(message='Project type is required.')],
        render_kw={'class': 'form-select'}
    )

    status = SelectField(
        'Project Status',
        choices=[
            ('Planning', 'Planning'),
            ('Active', 'Active'),
            ('On Hold', 'On Hold'),
            ('Completed', 'Completed'),
            ('Suspended', 'Suspended'),
            ('Closed', 'Closed'),
        ],
        default='Active',
        validators=[DataRequired(message='Project status is required.')],
        render_kw={'class': 'form-select'}
    )

    # Timeline
    start_date = DateField(
        'Start Date',
        validators=[DataRequired(message='Start date is required.')],
        render_kw={'class': 'form-control', 'type': 'date'}
    )

    end_date = DateField(
        'End Date',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'type': 'date'}
    )

    expected_completion_date = DateField(
        'Expected Completion Date',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'type': 'date'}
    )

    operational_shift = SelectField(
        'Operational Shift',
        choices=[
            ('', 'Select shift'),
            ('Morning', 'Morning (6 AM - 2 PM)'),
            ('Afternoon', 'Afternoon (2 PM - 10 PM)'),
            ('Night', 'Night (10 PM - 6 AM)'),
            ('24/7', '24/7 Operations'),
        ],
        validators=[Optional()],
        render_kw={'class': 'form-select'}
    )

    # Location
    country = SelectField(
        'Country',
        choices=[('', 'Select country'), ('India', 'India')],
        validators=[Optional()],
        render_kw={'class': 'form-select'}
    )

    state = StringField(
        'State',
        validators=[Optional(), Length(max=100)],
        render_kw={'class': 'form-control', 'placeholder': 'e.g., Uttar Pradesh'}
    )

    city = StringField(
        'City',
        validators=[Optional(), Length(max=100)],
        render_kw={'class': 'form-control', 'placeholder': 'e.g., Lucknow'}
    )

    pincode = StringField(
        'Pincode',
        validators=[Optional(), Regexp(r'^[0-9]{5,10}$', message='Pincode must be 5-10 digits.')],
        render_kw={'class': 'form-control', 'placeholder': '226001'}
    )

    full_address = TextAreaField(
        'Full Address',
        validators=[Optional(), Length(max=500)],
        render_kw={'class': 'form-control', 'rows': '3', 'placeholder': 'Enter complete operational address'}
    )

    # Operational Configuration
    deployment_allowed = BooleanField(
        'Deployment Allowed',
        default=True,
        render_kw={'class': 'form-check-input'}
    )

    attendance_required = BooleanField(
        'Attendance Required',
        default=True,
        render_kw={'class': 'form-check-input'}
    )

    gps_tracking_enabled = BooleanField(
        'GPS Tracking Enabled',
        default=False,
        render_kw={'class': 'form-check-input'}
    )

    realtime_monitoring_enabled = BooleanField(
        'Realtime Monitoring Enabled',
        default=False,
        render_kw={'class': 'form-check-input'}
    )

    geo_fencing_enabled = BooleanField(
        'Geo-Fencing Enabled',
        default=False,
        render_kw={'class': 'form-check-input'}
    )

    workflow_approval_enabled = BooleanField(
        'Workflow Approval Enabled',
        default=False,
        render_kw={'class': 'form-check-input'}
    )

    document_verification_required = BooleanField(
        'Document Verification Required',
        default=False,
        render_kw={'class': 'form-check-input'}
    )

    shift_based_attendance = BooleanField(
        'Shift-Based Attendance',
        default=False,
        render_kw={'class': 'form-check-input'}
    )

    # Resource Configuration
    max_vehicles = IntegerField(
        'Maximum Vehicles',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': '50', 'type': 'number', 'min': '1'}
    )

    max_drivers = IntegerField(
        'Maximum Drivers',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': '100', 'type': 'number', 'min': '1'}
    )

    deployment_capacity = IntegerField(
        'Deployment Capacity',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': '200', 'type': 'number', 'min': '1'}
    )

    required_vehicle_types = StringField(
        'Required Vehicle Types',
        validators=[Optional(), Length(max=255)],
        render_kw={'class': 'form-control', 'placeholder': 'e.g., Sedan, SUV, Truck'}
    )

    operational_capacity = IntegerField(
        'Operational Capacity',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': '500', 'type': 'number', 'min': '1'}
    )

    # Project Management
    project_manager = StringField(
        'Project Manager',
        validators=[Optional(), Length(max=150)],
        render_kw={'class': 'form-control', 'placeholder': 'Full name'}
    )

    operational_head = StringField(
        'Operational Head',
        validators=[Optional(), Length(max=150)],
        render_kw={'class': 'form-control', 'placeholder': 'Full name'}
    )

    contact_number = StringField(
        'Contact Number',
        validators=[
            Optional(),
            Regexp(r'^[0-9\-\+\s\(\)]{7,}$', message='Contact number format is invalid.')
        ],
        render_kw={'class': 'form-control', 'placeholder': '9876543210'}
    )

    operational_email = StringField(
        'Operational Email',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'operations@project.com'}
    )

    submit = SubmitField('Create Project', render_kw={'class': 'btn btn-gradient'})

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        # Set default start date to today
        if not self.start_date.data:
            self.start_date.data = date.today()

    def validate_project_code(self, field):
        """Custom validator for project code format"""
        code = field.data.strip().upper() if field.data else ''
        validate_project_code(code)

    def validate_project_name(self, field):
        """Custom validator for project name"""
        if field.data:
            validate_project_name(field.data)

    def validate_start_date(self, field):
        """Ensure start date is not in the past"""
        if field.data and field.data < date.today():
            raise ValidationError('Start date cannot be in the past.')

    def validate_operational_email(self, field):
        """Validate operational email format"""
        if field.data:
            validate_email(field.data)

    def validate(self, extra_validators=None):
        """Safe WTForms-compatible validation"""
        if not super().validate(extra_validators=extra_validators):
            return False

        # Validate hierarchy
        try:
            company_id = self.company_id.data
            circle_id = self.circle_id.data
            client_id = self.client_id.data
            validate_project_hierarchy(company_id, circle_id, client_id)
        except ValidationError as e:
            self.company_id.errors.append(str(e))
            return False

        # Validate dates
        try:
            validate_project_dates(
                self.start_date.data,
                self.end_date.data,
                self.expected_completion_date.data
            )
        except ValidationError as e:
            self.start_date.errors.append(str(e))
            return False

        # Validate project code uniqueness
        try:
            validate_project_code_unique(
                self.company_id.data,
                self.client_id.data,
                self.project_code.data
            )
        except ValidationError as e:
            self.project_code.errors.append(str(e))
            return False

        return True
