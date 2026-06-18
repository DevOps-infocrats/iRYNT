from datetime import date
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
    IntegerField,
    BooleanField,
    SubmitField,
)
from wtforms.validators import DataRequired, Optional, Length

from app.modules.vehicles.validators import (
    validate_vehicle_number,
    validate_vehicle_type,
    validate_vehicle_category,
    validate_vehicle_status,
    validate_phone,
)
from app.modules.vehicles.vehicle_status import (
    VEHICLE_TYPES,
    VEHICLE_CATEGORIES,
    VEHICLE_STATUS_CHOICES,
    COMPLIANCE_STATUS_CHOICES,
)


def make_year_choices():
    current_year = date.today().year
    return [('', 'Select year')] + [(str(y), str(y)) for y in range(current_year, current_year - 25, -1)]


class VehicleForm(FlaskForm):
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
        render_kw={'class': 'form-select select2'}
    )

    client_id = SelectField(
        'Client',
        choices=[],
        validators=[DataRequired(message='Client is required.')],
        render_kw={'class': 'form-select select2'}
    )

    project_id = SelectField(
        'Project',
        choices=[],
        validators=[DataRequired(message='Project is required.')],
        render_kw={'class': 'form-select select2'}
    )

    subzone_id = SelectField(
        'Subzone',
        choices=[],
        validators=[DataRequired(message='Subzone is required.')],
        render_kw={'class': 'form-select select2'}
    )

    vehicle_number = StringField(
        'Vehicle Number',
        filters=[lambda v: v.strip().upper() if v else v],
        validators=[
            validate_vehicle_number,
            Length(min=8, max=12, message='Vehicle number must be 8-12 characters.'),
        ],
        render_kw={'class': 'form-control', 'placeholder': 'UP32AB1234'}
    )

    vehicle_type = SelectField(
        'Vehicle Type',
        choices=VEHICLE_TYPES,
        validators=[validate_vehicle_type],
        render_kw={'class': 'form-select'}
    )

    vehicle_category = SelectField(
        'Vehicle Category',
        choices=VEHICLE_CATEGORIES,
        validators=[validate_vehicle_category],
        render_kw={'class': 'form-select'}
    )

    vehicle_brand = StringField(
        'Vehicle Brand',
        validators=[DataRequired(message='Vehicle brand is required.'), Length(max=80)],
        render_kw={'class': 'form-control', 'placeholder': 'Tata, Mahindra, Hyundai'}
    )

    vehicle_model = StringField(
        'Vehicle Model',
        validators=[DataRequired(message='Vehicle model is required.'), Length(max=80)],
        render_kw={'class': 'form-control', 'placeholder': 'e.g., Ace, Bolero Pickup, Eeco'}
    )

    manufacturing_year = SelectField(
        'Manufacturing Year',
        choices=make_year_choices(),
        validators=[DataRequired(message='Manufacturing year is required.')],
        render_kw={'class': 'form-select'}
    )

    chassis_number = StringField(
        'Chassis Number',
        filters=[lambda v: v.strip() if v and v.strip() else None],
        validators=[Optional(), Length(max=100)],
        render_kw={'class': 'form-control', 'placeholder': 'Optional chassis number'}
    )

    engine_number = StringField(
        'Engine Number',
        filters=[lambda v: v.strip() if v and v.strip() else None],
        validators=[Optional(), Length(max=100)],
        render_kw={'class': 'form-control', 'placeholder': 'Optional engine number'}
    )

    owner_name = StringField(
        'Owner Name',
        validators=[Optional(), Length(max=120)],
        render_kw={'class': 'form-control', 'placeholder': 'Owner or fleet manager name'}
    )

    owner_phone = StringField(
        'Owner Phone',
        validators=[Optional(), validate_phone],
        render_kw={'class': 'form-control', 'placeholder': '10-digit mobile number'}
    )

    vendor_name = StringField(
        'Vendor Name',
        validators=[Optional(), Length(max=120)],
        render_kw={'class': 'form-control', 'placeholder': 'Vendor or leasing company'}
    )

    vendor_contact = StringField(
        'Vendor Contact',
        validators=[Optional(), validate_phone],
        render_kw={'class': 'form-control', 'placeholder': 'Vendor mobile number'}
    )

    gps_enabled = BooleanField('GPS Enabled', default=True, render_kw={'class': 'form-check-input'})
    realtime_tracking_enabled = BooleanField('Realtime Tracking Enabled', default=True, render_kw={'class': 'form-check-input'})
    deployment_allowed = BooleanField('Deployment Allowed', default=True, render_kw={'class': 'form-check-input'})
    attendance_linked = BooleanField('Attendance Linked', default=False, render_kw={'class': 'form-check-input'})
    fuel_tracking_enabled = BooleanField('Fuel Tracking Enabled', default=False, render_kw={'class': 'form-check-input'})
    geo_fencing_enabled = BooleanField('Geo-Fencing Enabled', default=False, render_kw={'class': 'form-check-input'})
    incident_monitoring_enabled = BooleanField('Incident Monitoring Enabled', default=False, render_kw={'class': 'form-check-input'})
    maintenance_tracking_enabled = BooleanField('Maintenance Tracking Enabled', default=False, render_kw={'class': 'form-check-input'})

    load_capacity = IntegerField(
        'Load Capacity (kg)',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'e.g., 1000', 'type': 'number', 'min': '0'}
    )

    passenger_capacity = IntegerField(
        'Passenger Capacity',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'e.g., 2', 'type': 'number', 'min': '0'}
    )

    fuel_capacity = IntegerField(
        'Fuel Capacity (L)',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'e.g., 45', 'type': 'number', 'min': '0'}
    )

    operational_capacity = IntegerField(
        'Operational Capacity',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'placeholder': 'e.g., 500', 'type': 'number', 'min': '0'}
    )

    status = SelectField(
        'Vehicle Status',
        choices=VEHICLE_STATUS_CHOICES,
        default='Available',
        validators=[validate_vehicle_status],
        render_kw={'class': 'form-select'}
    )

    insurance_status = SelectField(
        'Insurance Status',
        choices=COMPLIANCE_STATUS_CHOICES,
        default='Valid',
        validators=[Optional()],
        render_kw={'class': 'form-select'}
    )

    fitness_status = SelectField(
        'Fitness Status',
        choices=COMPLIANCE_STATUS_CHOICES,
        default='Valid',
        validators=[Optional()],
        render_kw={'class': 'form-select'}
    )

    permit_status = SelectField(
        'Permit Status',
        choices=COMPLIANCE_STATUS_CHOICES,
        default='Valid',
        validators=[Optional()],
        render_kw={'class': 'form-select'}
    )

    puc_status = SelectField(
        'PUC Status',
        choices=COMPLIANCE_STATUS_CHOICES,
        default='Valid',
        validators=[Optional()],
        render_kw={'class': 'form-select'}
    )

    verification_status = SelectField(
        'Verification Status',
        choices=COMPLIANCE_STATUS_CHOICES,
        default='Valid',
        validators=[Optional()],
        render_kw={'class': 'form-select'}
    )

    assigned_driver = StringField(
        'Assigned Driver',
        validators=[Optional(), Length(max=120)],
        render_kw={'class': 'form-control', 'placeholder': 'Driver name or identifier'}
    )

    current_deployment = StringField(
        'Current Deployment',
        validators=[Optional(), Length(max=150)],
        render_kw={'class': 'form-control', 'placeholder': 'Current assignment or route'}
    )

    submit = SubmitField('Save Vehicle', render_kw={'class': 'btn btn-gradient-primary btn-lg'})
