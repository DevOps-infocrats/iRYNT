import re
from wtforms.validators import ValidationError


def validate_subzone_code(form, field):
    if not field.data:
        return
    value = field.data.strip().upper()
    if not re.match(r'^[A-Z0-9_-]+$', value):
        raise ValidationError('Use A-Z, 0-9, underscore, or hyphen only.')
    if len(value) < 2 or len(value) > 20:
        raise ValidationError('Subzone code must be 2-20 characters.')
    field.data = value


def validate_subzone_name(form, field):
    if not field.data:
        return
    value = field.data.strip()
    if len(value) < 3 or len(value) > 150:
        raise ValidationError('Subzone name must be 3-150 characters.')
    field.data = value

