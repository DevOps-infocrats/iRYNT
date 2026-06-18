from app.modules.auth.models import User
from app.modules.drivers.models import DriverLicense, DriverProfile
from app.modules.drivers.repository import DriverRepository


class DriverService:
    def __init__(self):
        self.repository = DriverRepository()

    def get_filter_payload(self, filters=None):
        filters = filters or {}
        return {
            'companies': self.get_company_choices(include_all=True),
            'circles': self.get_circle_choices(filters.get('company_id'), include_all=True),
            'status_options': self.repository.get_status_options(),
        }

    def get_company_choices(self, include_all=True):
        companies = self.repository.get_companies()
        label = 'All companies' if include_all else 'Select company'
        choices = [('', label)]
        return choices + [(company.id, f"{company.company_name} ({company.company_code})") for company in companies]

    def get_circle_choices(self, company_id=None, include_all=True):
        circles = self.repository.get_circles(company_id)
        label = 'All circles' if include_all else 'Select circle'
        if include_all or company_id:
            return [('', label)] + [(circle.id, f"{circle.circle_name} ({circle.circle_code})") for circle in circles]
        return [('', label)]

    def get_client_choices(self, circle_id=None, include_all=False):
        clients = self.repository.get_clients(circle_id)
        label = 'All clients' if include_all else 'Select client'
        if include_all or circle_id:
            return [('', label)] + [(client.id, f"{client.client_name} ({client.client_code})") for client in clients]
        return [('', label)]

    def get_project_choices(self, client_id=None, include_all=False):
        projects = self.repository.get_projects(client_id)
        label = 'All projects' if include_all else 'Select project'
        if include_all or client_id:
            return [('', label)] + [(project.id, f"{project.project_name} ({project.project_code})") for project in projects]
        return [('', label)]

    def get_subzone_choices(self, project_id=None, include_all=False):
        subzones = self.repository.get_subzones(project_id)
        label = 'All subzones' if include_all else 'Select subzone'
        if include_all or project_id:
            return [('', label)] + [(subzone.id, f"{subzone.subzone_name} ({subzone.subzone_code})") for subzone in subzones]
        return [('', label)]

    def list_drivers(self, filters, page, per_page):
        offset = (page - 1) * per_page
        drivers, total = self.repository.list_drivers(filters, offset, per_page)
        return drivers, total

    def get_driver_profile(self, driver_id):
        return self.repository.get_driver_profile(driver_id)

    def get_status_choices(self):
        return self.repository.get_status_options()

    def find_user_by_identifier(self, identifier):
        return User.query.filter((User.email == identifier) | (User.username == identifier)).first()

    def driver_code_exists(self, driver_code):
        return DriverProfile.query.filter_by(driver_code=driver_code).first() is not None

    def license_number_exists(self, license_number):
        return DriverLicense.query.filter_by(license_number=license_number).first() is not None

    def create_driver_profile(self, payload):
        driver_profile = DriverProfile(
            user_id=payload['user_id'],
            driver_code=payload.get('driver_code'),
            circle_id=payload.get('circle_id'),
            client_id=payload.get('client_id'),
            project_id=payload.get('project_id'),
            subzone_id=payload.get('subzone_id'),
            dob=payload.get('dob'),
            gender=payload.get('gender'),
            blood_group=payload.get('blood_group'),
            nationality=payload.get('nationality'),
            address=payload.get('address'),
            emergency_contact_name=payload.get('emergency_contact_name'),
            emergency_contact_phone=payload.get('emergency_contact_phone'),
            experience_years=payload.get('experience_years'),
            join_date=payload.get('join_date'),
            license_status='Pending',
            compliance_status='Pending',
            active=True,
        )
        from app.extensions import db
        db.session.add(driver_profile)
        db.session.commit()

        license_number = payload.get('license_number')
        if license_number:
            license_record = DriverLicense(
                driver_id=driver_profile.id,
                license_number=license_number.strip() if isinstance(license_number, str) else license_number,
                vehicle_classes=payload.get('vehicle_classes'),
                issue_date=payload.get('issue_date'),
                expiry_date=payload.get('expiry_date'),
            )
            db.session.add(license_record)
            db.session.commit()

        return driver_profile
