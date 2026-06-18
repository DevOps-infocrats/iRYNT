import sys
import os
import io
import datetime

sys.path.insert(0, os.getcwd())

from app import create_app
from app.extensions import db
from app.modules.auth.models import User
from app.modules.companies.models import Company
from app.modules.circles.models import Circle
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.subzones.models import Subzone
from app.modules.drivers.forms import DriverCreateForm
from app.modules.drivers.services import DriverService

app = create_app('testing')

with app.app_context():
    # 1. Create setup data
    company = Company(
        company_name='Test Logistics Ltd',
        company_code='TESTLOG',
        gst_number='29ABCDE1234F2Z5',
        pan_number='ABCDE1234F',
        email='info@testlogistics.com',
        phone='9123456789',
        pincode='226001',
        status='Active'
    )
    db.session.add(company)
    db.session.commit()

    circle = Circle(
        company_id=company.id,
        circle_code='TESTCIR',
        circle_name='Test Circle',
        email='circle@testlogistics.com',
        phone='9123456790',
        status='Active'
    )
    db.session.add(circle)
    db.session.commit()

    client_obj = Client(
        company_id=company.id,
        circle_id=circle.id,
        client_code='TESTCL',
        client_name='Test Client',
        email='client@testlogistics.com',
        phone='9123456791',
        status='Active'
    )
    db.session.add(client_obj)
    db.session.commit()

    project = Project(
        company_id=company.id,
        circle_id=circle.id,
        client_id=client_obj.id,
        project_code='TESTPRJ',
        project_name='Test Project',
        project_type='Logistics',
        status='Active',
        start_date=datetime.date.today(),
        end_date=datetime.date.today() + datetime.timedelta(days=30),
        expected_completion_date=datetime.date.today() + datetime.timedelta(days=60),
        pincode='226001',
        deployment_allowed=True,
        attendance_required=True
    )
    db.session.add(project)
    db.session.commit()

    subzone = Subzone(
        company_id=company.id,
        circle_id=circle.id,
        client_id=client_obj.id,
        project_id=project.id,
        subzone_code='TESTSZ',
        subzone_name='Test Subzone',
        status='Active',
        pincode='226001',
        geo_fencing_enabled=True,
        allowed_radius=500,
        attendance_radius=250,
        gps_validation=True,
        attendance_required=True,
        deployment_allowed=True
    )
    db.session.add(subzone)
    db.session.commit()

    print("Company ID:", company.id)
    print("Circle ID:", circle.id)
    print("Client ID:", client_obj.id)
    print("Project ID:", project.id)
    print("Subzone ID:", subzone.id)
    
    # 2. Setup POST data
    driver_data = {
        'identifier': 'autodriver1',
        'company_id': company.id,
        'circle_id': circle.id,
        'client_id': client_obj.id,
        'project_id': project.id,
        'subzone_id': subzone.id,
        'gender': 'Male',
        'nationality': 'Indian',
        'address': 'Driver Address',
        'emergency_contact_name': 'Emergency',
        'emergency_contact_phone': '9123456793',
        'experience_years': '2',
        'join_date': datetime.date.today().isoformat(),
        'license_number': 'DL1234567890123',
        'vehicle_classes': 'LMV',
        'issue_date': datetime.date.today().isoformat(),
        'expiry_date': (datetime.date.today() + datetime.timedelta(days=365)).isoformat(),
        'document_type': 'Driving License',
        'submit': 'Create Driver Profile',
    }
    
    with app.test_request_context(method='POST', data=driver_data):
        import flask
        from werkzeug.datastructures import FileStorage, MultiDict
        
        # Simulate file fields using a mutable MultiDict
        files = MultiDict()
        files.add('driving_license_file', FileStorage(io.BytesIO(b"dummy DL content"), "license.pdf", "driving_license_file"))
        files.add('aadhaar_file', FileStorage(io.BytesIO(b"dummy Aadhaar content"), "aadhaar.pdf", "aadhaar_file"))
        files.add('pan_file', FileStorage(io.BytesIO(b"dummy PAN content"), "pan.pdf", "pan_file"))
        flask.request.files = files
        
        service = DriverService()
        form = DriverCreateForm()
        
        # Populate choices
        form.company_id.choices = service.get_company_choices(include_all=False)
        form.circle_id.choices = service.get_circle_choices(company.id, include_all=False)
        form.client_id.choices = service.get_client_choices(circle.id, include_all=False)
        form.project_id.choices = service.get_project_choices(client_obj.id, include_all=False)
        form.subzone_id.choices = service.get_subzone_choices(project.id, include_all=False)
        
        is_valid = form.validate()
        print("Form Valid?", is_valid)
        print("Form Errors:", form.errors)
