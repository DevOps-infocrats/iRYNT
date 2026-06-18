"""
Deployment Forms

Web forms for creating and managing vehicle deployments.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, TextAreaField, IntegerField, FloatField,
    BooleanField, SubmitField, DateField
)
from wtforms.validators import DataRequired, Optional, Length


class DeploymentForm(FlaskForm):
    """Form for creating/editing deployments"""

    vehicle_id = SelectField(
        'Vehicle',
        choices=[],
        validators=[DataRequired(message='Vehicle is required.')],
        render_kw={'class': 'form-select select2'}
    )

    driver_id = SelectField(
        'Driver',
        choices=[('', 'Select driver (optional)')],
        validators=[Optional()],
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

    deployment_type = SelectField(
        'Deployment Type',
        choices=[
            ('Standard', 'Standard Route'),
            ('Express', 'Express Delivery'),
            ('Special', 'Special Assignment'),
            ('Emergency', 'Emergency Response'),
        ],
        default='Standard',
        validators=[DataRequired()],
        render_kw={'class': 'form-select'}
    )

    route_name = StringField(
        'Route Name',
        validators=[Optional(), Length(max=255)],
        render_kw={'class': 'form-control', 'placeholder': 'e.g., North Zone Route A'}
    )

    pickup_location = StringField(
        'Pickup Location',
        validators=[Optional(), Length(max=255)],
        render_kw={'class': 'form-control', 'placeholder': 'Starting point'}
    )

    dropoff_location = StringField(
        'Dropoff Location',
        validators=[Optional(), Length(max=255)],
        render_kw={'class': 'form-control', 'placeholder': 'Ending point'}
    )

    vehicle_fitness_verified = BooleanField(
        'Vehicle Fitness Verified',
        default=False,
        render_kw={'class': 'form-check-input'}
    )

    driver_license_verified = BooleanField(
        'Driver License Verified',
        default=False,
        render_kw={'class': 'form-check-input'}
    )

    insurance_verified = BooleanField(
        'Insurance Verified',
        default=False,
        render_kw={'class': 'form-check-input'}
    )

    safety_checklist_completed = BooleanField(
        'Safety Checklist Completed',
        default=False,
        render_kw={'class': 'form-check-input'}
    )

    special_instructions = TextAreaField(
        'Special Instructions',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes for this deployment'}
    )

    notes = TextAreaField(
        'Notes',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'rows': 2}
    )

    submit = SubmitField('Create Deployment', render_kw={'class': 'btn btn-gradient-primary btn-lg'})


class DeploymentApprovalForm(FlaskForm):
    """Form for approving deployments"""

    approval_action = SelectField(
        'Action',
        choices=[
            ('approve', 'Approve'),
            ('reject', 'Reject'),
            ('escalate', 'Escalate'),
        ],
        validators=[DataRequired()],
        render_kw={'class': 'form-select'}
    )

    reason = TextAreaField(
        'Reason/Comments',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'rows': 3, 'placeholder': 'Approval decision comments'}
    )

    submit = SubmitField('Submit', render_kw={'class': 'btn btn-primary btn-lg'})


class DeploymentCompletionForm(FlaskForm):
    """Form for completing deployments"""

    distance_km = FloatField(
        'Distance (km)',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'type': 'number', 'step': '0.1', 'min': '0'}
    )

    duration_minutes = IntegerField(
        'Duration (minutes)',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'type': 'number', 'min': '0'}
    )

    fuel_consumed = FloatField(
        'Fuel Consumed (liters)',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'type': 'number', 'step': '0.1', 'min': '0'}
    )

    notes = TextAreaField(
        'Completion Notes',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'rows': 3}
    )

    submit = SubmitField('Complete Deployment', render_kw={'class': 'btn btn-success btn-lg'})


class AssignDriverForm(FlaskForm):
    """Form for assigning a driver to a vehicle"""

    vehicle_id = SelectField(
        'Vehicle',
        choices=[],
        validators=[DataRequired(message='Vehicle is required.')],
        render_kw={'class': 'form-select select2'}
    )

    driver_id = SelectField(
        'Driver',
        choices=[('', 'Select driver')],
        validators=[DataRequired(message='Driver is required.')],
        render_kw={'class': 'form-select select2'}
    )

    submit = SubmitField('Assign Driver', render_kw={'class': 'btn btn-primary btn-lg'})


class HelperAssignmentForm(FlaskForm):
    """Form for helper assignments"""

    helper_id = SelectField(
        'Helper *',
        choices=[],
        validators=[DataRequired(message='Helper is required.')],
        render_kw={'class': 'form-select select2'}
    )

    circle_id = SelectField(
        'Circle *',
        choices=[],
        validators=[DataRequired(message='Circle is required.')],
        render_kw={'class': 'form-select select2'}
    )

    project_id = SelectField(
        'Project *',
        choices=[],
        validators=[DataRequired(message='Project is required.')],
        render_kw={'class': 'form-select select2'}
    )

    subzone_id = SelectField(
        'Subzone *',
        choices=[],
        validators=[DataRequired(message='Subzone is required.')],
        render_kw={'class': 'form-select select2'}
    )

    shift = SelectField(
        'Shift',
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

    start_date = DateField(
        'Start Date *',
        validators=[DataRequired(message='Start date is required.')],
        render_kw={'class': 'form-control', 'type': 'date'}
    )

    end_date = DateField(
        'End Date',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'type': 'date'}
    )

    status = SelectField(
        'Status',
        choices=[
            ('Active', 'Active'),
            ('Ended', 'Ended'),
        ],
        default='Active',
        validators=[DataRequired()],
        render_kw={'class': 'form-select'}
    )

    remarks = TextAreaField(
        'Remarks',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'rows': 3}
    )

    assigned_driver_id = SelectField(
        'Assigned Driver',
        choices=[('', 'Select driver (optional)')],
        validators=[Optional()],
        render_kw={'class': 'form-select select2'}
    )

    assigned_vehicle_id = SelectField(
        'Assigned Vehicle',
        choices=[('', 'Select vehicle (optional)')],
        validators=[Optional()],
        render_kw={'class': 'form-select select2'}
    )

    submit = SubmitField('Save Assignment', render_kw={'class': 'btn btn-primary btn-lg'})
