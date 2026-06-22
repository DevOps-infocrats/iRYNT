from marshmallow import ValidationError
from app.domain.auth.policies.auth_policy import has_role
from app.modules.drivers.models import DriverProfile

def validate_role_attendance_requirements(user, driver_profile, action, data):
    """
    Validates role-specific requirements:
    - Helpers: Must provide a selfie when checking in.
    - Drivers: Must provide an odometer reading when checking in or out.
    """
    is_helper = has_role(user, 'Helper')
    is_driver = has_role(user, 'Driver')

    if is_helper:
        if action == 'check_in':
            has_selfie = data.get('selfie_data') or data.get('selfie_file')
            if not has_selfie:
                raise ValidationError('A selfie is required for Helper check-in.')
        # Odometer is ignored/not required for Helpers

    elif is_driver:
        # Drivers must provide an odometer reading
        odometer = data.get('odometer')
        if odometer is None:
            raise ValidationError('Odometer reading is required for Driver attendance.')
        try:
            float(odometer)
        except ValueError:
            raise ValidationError('Odometer reading must be a valid number.')
