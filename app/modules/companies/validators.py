import re


COMPANY_NAME_PATTERN = re.compile(r'^[A-Za-z0-9 .,&\-()]+$')
COMPANY_CODE_PATTERN = re.compile(r'^[A-Z0-9_-]{2,20}$')
GST_NUMBER_PATTERN = re.compile(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$')
PAN_NUMBER_PATTERN = re.compile(r'^[A-Z]{5}[0-9]{4}[A-Z]$')
PHONE_PATTERN = re.compile(r'^[6-9]\d{9}$')
PINCODE_PATTERN = re.compile(r'^\d{6}$')


def validate_company_name(value):
    if not value or not COMPANY_NAME_PATTERN.match(value):
        return False
    return True


def validate_company_code(value):
    if not value or not COMPANY_CODE_PATTERN.match(value):
        return False
    return True


def validate_gst_number(value):
    if not value:
        return True
    return bool(GST_NUMBER_PATTERN.match(value))


def validate_pan_number(value):
    if not value:
        return True
    return bool(PAN_NUMBER_PATTERN.match(value))


def validate_phone(value):
    if not value:
        return True
    return bool(PHONE_PATTERN.match(value))


def validate_pincode(value):
    return bool(PINCODE_PATTERN.match(value))
