from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, Regexp

from app.modules.subzones.validators import validate_subzone_code, validate_subzone_name


class SubzoneForm(FlaskForm):
    company_id = SelectField(
        'Company',
        choices=[],
        validators=[DataRequired(message='Company is required.')],
        render_kw={'class': 'form-select select2'}
    )

    circle_id = SelectField(
        'Circle',
        choices=[],
        validators=[DataRequired(message='Circle is required.')],
        render_kw={'class': 'form-select select2', 'disabled': 'disabled'}
    )

    client_id = SelectField(
        'Client',
        choices=[],
        validators=[DataRequired(message='Client is required.')],
        render_kw={'class': 'form-select select2', 'disabled': 'disabled'}
    )

    project_id = SelectField(
        'Project',
        choices=[],
        validators=[DataRequired(message='Project is required.')],
        render_kw={'class': 'form-select select2', 'disabled': 'disabled'}
    )

    subzone_code = StringField(
        'Subzone Code',
        validators=[
            DataRequired(message='Subzone code is required.'),
            Length(min=2, max=20, message='Subzone code must be 2-20 characters.'),
            Regexp(r'^[A-Z0-9_-]+$', message='Use A-Z, 0-9, underscore, or hyphen only.'),
            validate_subzone_code,
        ],
        render_kw={'class': 'form-control', 'placeholder': 'e.g., LKO_SOUTH_01', 'autocomplete': 'off'}
    )

    subzone_name = StringField(
        'Subzone Name',
        validators=[
            DataRequired(message='Subzone name is required.'),
            Length(min=3, max=150, message='Subzone name must be 3-150 characters.'),
            validate_subzone_name,
        ],
        render_kw={'class': 'form-control', 'placeholder': 'e.g., Warehouse Cluster A'}
    )

    subzone_type = SelectField(
        'Subzone Type',
        choices=[
            ('', 'Select subzone type'),
            ('Delivery Zone', 'Delivery Zone'),
            ('Warehouse Zone', 'Warehouse Zone'),
            ('Transport Zone', 'Transport Zone'),
            ('Cluster Zone', 'Cluster Zone'),
            ('Operational Zone', 'Operational Zone'),
            ('Field Zone', 'Field Zone'),
        ],
        validators=[DataRequired(message='Subzone type is required.')],
        render_kw={'class': 'form-select'}
    )

    status = SelectField(
        'Operational Status',
        choices=[
            ('Active', 'Active'),
            ('Inactive', 'Inactive'),
            ('Restricted', 'Restricted'),
            ('Maintenance', 'Maintenance'),
            ('Closed', 'Closed'),
        ],
        default='Active',
        validators=[DataRequired(message='Status is required.')],
        render_kw={'class': 'form-select'}
    )

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
        render_kw={'class': 'form-control', 'rows': '3', 'placeholder': 'Enter operational address'}
    )

    latitude = StringField(
        'Latitude',
        validators=[Optional(), Length(max=20)],
        render_kw={'class': 'form-control', 'placeholder': '26.8467'}
    )

    longitude = StringField(
        'Longitude',
        validators=[Optional(), Length(max=20)],
        render_kw={'class': 'form-control', 'placeholder': '80.9462'}
    )

    geo_fencing_enabled = BooleanField(
        'Geo-Fencing Enabled',
        default=False,
        render_kw={'class': 'form-check-input'}
    )

    allowed_radius = IntegerField(
        'Allowed Radius (meters)',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'e.g. 500'}
    )

    attendance_radius = IntegerField(
        'Attendance Radius',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'e.g. 250'}
    )

    gps_validation = BooleanField(
        'GPS Validation',
        default=True,
        render_kw={'class': 'form-check-input'}
    )

    restricted_movement_detection = BooleanField(
        'Restricted Movement Detection',
        default=False,
        render_kw={'class': 'form-check-input'}
    )

    max_vehicles = IntegerField(
        'Maximum Vehicles',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'e.g. 120'}
    )

    max_drivers = IntegerField(
        'Maximum Drivers',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'e.g. 95'}
    )

    shift_operations_enabled = BooleanField(
        'Shift Operations Enabled',
        default=True,
        render_kw={'class': 'form-check-input'}
    )

    attendance_required = BooleanField(
        'Attendance Required',
        default=True,
        render_kw={'class': 'form-check-input'}
    )

    deployment_allowed = BooleanField(
        'Deployment Allowed',
        default=True,
        render_kw={'class': 'form-check-input'}
    )

    realtime_tracking_enabled = BooleanField(
        'Realtime Tracking Enabled',
        default=False,
        render_kw={'class': 'form-check-input'}
    )

    workflow_approval_enabled = BooleanField(
        'Workflow Approval Enabled',
        default=False,
        render_kw={'class': 'form-check-input'}
    )

    incident_reporting_enabled = BooleanField(
        'Incident Reporting Enabled',
        default=False,
        render_kw={'class': 'form-check-input'}
    )

    vehicle_capacity = IntegerField(
        'Vehicle Capacity',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'e.g. 80'}
    )

    driver_capacity = IntegerField(
        'Driver Capacity',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'e.g. 85'}
    )

    parking_capacity = IntegerField(
        'Parking Capacity',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'e.g. 40'}
    )

    operational_capacity = IntegerField(
        'Operational Capacity',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'e.g. 100'}
    )
