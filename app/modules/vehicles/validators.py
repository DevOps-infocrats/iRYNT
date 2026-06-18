import re
from wtforms.validators import ValidationError
from app.modules.vehicles.vehicle_status import VEHICLE_TYPES, VEHICLE_CATEGORIES, VEHICLE_STATUS_CHOICES

VEHICLE_NUMBER_REGEX = re.compile(r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{4}$')
PHONE_REGEX = re.compile(r'^[6-9]\d{9}$')


def validate_vehicle_number(form, field):
    if not field.data:
        raise ValidationError('Vehicle number is required.')
    value = field.data.strip().upper()
    if not VEHICLE_NUMBER_REGEX.match(value):
        raise ValidationError('Vehicle number must follow the format UP32AB1234.')


def validate_vehicle_type(form, field):
    if field.data not in [choice[0] for choice in VEHICLE_TYPES if choice[0]]:
        raise ValidationError('Select a valid vehicle type.')


def validate_vehicle_category(form, field):
    if field.data not in [choice[0] for choice in VEHICLE_CATEGORIES if choice[0]]:
        raise ValidationError('Select a valid vehicle category.')


def validate_vehicle_status(form, field):
    if field.data not in [choice[0] for choice in VEHICLE_STATUS_CHOICES if choice[0]]:
        raise ValidationError('Select a valid vehicle status.')


def validate_phone(form, field):
    if field.data:
        if not PHONE_REGEX.match(field.data.strip()):
            raise ValidationError('Enter a valid 10-digit mobile number starting with 6-9.')

