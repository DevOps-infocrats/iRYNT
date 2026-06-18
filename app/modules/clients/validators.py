import re

from app.modules.companies.validators import validate_phone


CLIENT_NAME_PATTERN = re.compile(r'^[A-Za-z0-9 .,&\-()]+$')
CLIENT_CODE_PATTERN = re.compile(r'^[A-Z0-9_-]{2,20}$')


def validate_client_name(value: str) -> bool:
    if not value:
        return False
    return bool(CLIENT_NAME_PATTERN.match(value)) and 3 <= len(value) <= 150


def validate_client_code(value: str) -> bool:
    if not value:
        return False
    return bool(CLIENT_CODE_PATTERN.match(value))


def validate_client_phone(value: str) -> bool:
    return validate_phone(value)
