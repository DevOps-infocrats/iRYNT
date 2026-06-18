import re
from wtforms import ValidationError
from app.modules.projects.models import Project
from app.modules.clients.models import Client
from app.modules.circles.models import Circle
from app.modules.companies.models import Company


def validate_project_code(code):
    """Validate project code format: ^[A-Z0-9_-]+$"""
    if not code:
        raise ValidationError('Project code is required.')
    
    code = code.strip().upper()
    if not re.match(r'^[A-Z0-9_-]{2,20}$', code):
        raise ValidationError('Project code must be 2-20 characters, using A-Z, 0-9, underscore (_), or hyphen (-).')
    
    return code


def validate_project_code_unique(company_id, client_id, code):
    """Check if project code is unique within client"""
    if not code:
        return True
    
    code = code.strip().upper()
    exists = Project.query.filter_by(
        company_id=company_id,
        client_id=client_id,
        project_code=code,
        status='Active'
    ).first()
    
    if exists:
        raise ValidationError('Project code already exists for this client.')
    
    return True


def validate_project_name(name):
    """Validate project name"""
    if not name:
        raise ValidationError('Project name is required.')
    
    name = name.strip()
    if len(name) < 3 or len(name) > 150:
        raise ValidationError('Project name must be between 3 and 150 characters.')
    
    return name


def validate_project_hierarchy(company_id, circle_id, client_id):
    """Validate company-circle-client hierarchy"""
    if not all([company_id, circle_id, client_id]):
        raise ValidationError('Company, circle, and client are required.')
    
    company = Company.query.filter_by(id=company_id, status='Active').first()
    if not company:
        raise ValidationError('Selected company is not valid or inactive.')
    
    circle = Circle.query.filter_by(id=circle_id, company_id=company_id, status='Active').first()
    if not circle:
        raise ValidationError('Selected circle does not belong to the company or is inactive.')
    
    client = Client.query.filter_by(id=client_id, company_id=company_id, circle_id=circle_id, status='Active').first()
    if not client:
        raise ValidationError('Selected client does not belong to the company/circle or is inactive.')
    
    return True


def validate_project_dates(start_date, end_date, expected_completion_date):
    """Validate project date logic"""
    if not start_date:
        raise ValidationError('Start date is required.')
    
    if end_date and end_date < start_date:
        raise ValidationError('End date cannot be before start date.')
    
    if expected_completion_date and expected_completion_date < start_date:
        raise ValidationError('Expected completion date cannot be before start date.')
    
    return True


def validate_project_type(project_type):
    """Validate project type"""
    valid_types = [
        'Logistics',
        'Transportation',
        'Delivery',
        'Fleet Operations',
        'Warehouse Operations',
        'Field Operations',
    ]
    
    if project_type not in valid_types:
        raise ValidationError('Invalid project type selected.')
    
    return True


def validate_project_status(status):
    """Validate project status"""
    valid_statuses = [
        'Planning',
        'Active',
        'On Hold',
        'Completed',
        'Suspended',
        'Closed',
    ]
    
    if status not in valid_statuses:
        raise ValidationError('Invalid project status selected.')
    
    return True


def validate_contact_number(phone):
    """Validate contact number"""
    if phone and not re.match(r'^[0-9\-\+\s\(\)]{7,}$', phone):
        raise ValidationError('Contact number format is invalid.')
    
    return True


def validate_email(email):
    """Validate email"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if email and not re.match(email_pattern, email):
        raise ValidationError('Email format is invalid.')
    
    return True


def validate_pincode(pincode):
    """Validate pincode"""
    if pincode and not re.match(r'^[0-9]{5,10}$', pincode):
        raise ValidationError('Pincode must be 5-10 digits.')
    
    return True


def validate_integer_positive(value):
    """Validate positive integer"""
    if value is not None and value < 0:
        raise ValidationError('Value must be a positive number.')
    
    return True

