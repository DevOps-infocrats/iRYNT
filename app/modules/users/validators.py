import re

from wtforms import ValidationError

PHONE_REGEX = re.compile(r'^\+?[0-9\s\-]{7,24}$')


def validate_phone(form, field):
    if field.data and not PHONE_REGEX.match(field.data.strip()):
        raise ValidationError('Enter a valid phone number.')
