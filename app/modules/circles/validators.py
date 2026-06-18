import re


def validate_circle_code(value: str) -> bool:
    if not value:
        return False
    return bool(re.match(r'^[A-Z0-9_-]{2,20}$', value))


def validate_circle_name(value: str) -> bool:
    if not value:
        return False
    return 3 <= len(value) <= 150
# auto-generated placeholder
