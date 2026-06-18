import datetime
import os
import sys
import io

sys.path.insert(0, os.getcwd())

from app import create_app
from app.modules.auth.models import User

app = create_app('testing')

with app.app_context():
    admin = User.query.filter_by(username='superadmin').first()
    if not admin:
        raise RuntimeError('superadmin user not found')

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['_user_id'] = admin.id

    def post(path, data):
        resp = client.post(path, data=data, follow_redirects=True)
        print(f'POST {path} -> {resp.status_code}')
        print(resp.data.decode('utf-8')[:800])
        return resp

    # Create company
    company_data = {
        'company_name': 'Test Logistics Ltd',
        'company_code': 'TESTLOG',
        'gst_number': '29ABCDE1234F2Z5',
        'pan_number': 'ABCDE1234F',
        'email': 'info@testlogistics.com',
        'phone': '9123456789',
        'country_id': 'IN',
        'state_id': 'UP',
        'city_id': 'LKO',
        'pincode': '226001',
        'status': 'Active',
        'submit': 'Save Company',
    }
    post('/companies/create', company_data)

    from app.modules.companies.models import Company
    company = Company.query.filter_by(company_code='TESTLOG').first()
    print('Company exists:', bool(company), getattr(company, 'id', None))

    # Create circle
    circle_data = {
        'company_id': company.id,
        'circle_code': 'TESTCIR',
        'circle_name': 'Test Circle',
        'regional_manager': 'RM Test',
        'email': 'circle@testlogistics.com',
        'phone': '9123456790',
        'address': 'Test Circle Address',
        'status': 'Active',
        'submit': 'Save Circle',
    }
    post('/circles/create', circle_data)
    from app.modules.circles.models import Circle
    circle = Circle.query.filter_by(circle_code='TESTCIR').first()
    print('Circle exists:', bool(circle), getattr(circle, 'id', None))

    # Create client
    client_data = {
        'company_id': company.id,
        'circle_id': circle.id,
        'client_code': 'TESTCL',
        'client_name': 'Test Client',
        'primary_contact': 'Client Contact',
        'email': 'client@testlogistics.com',
        'phone': '9123456791',
        'address': 'Client Address',
        'status': 'Active',
        'submit': 'Save Client',
    }
    post('/clients/create', client_data)
    from app.modules.clients.models import Client
    client_obj = Client.query.filter_by(client_code='TESTCL').first()
    print('Client exists:', bool(client_obj), getattr(client_obj, 'id', None))

    # Create project
    project_data = {
        'company_id': company.id,
        'circle_id': circle.id,
        'client_id': client_obj.id,
        'project_code': 'TESTPRJ',
        'project_name': 'Test Project',
        'project_type': 'Logistics',
        'status': 'Active',
        'start_date': datetime.date.today().isoformat(),
        'end_date': (datetime.date.today() + datetime.timedelta(days=30)).isoformat(),
        'expected_completion_date': (datetime.date.today() + datetime.timedelta(days=60)).isoformat(),
        'operational_shift': 'Morning',
        'country': 'India',
        'state': 'Uttar Pradesh',
        'city': 'Lucknow',
        'pincode': '226001',
        'full_address': 'Project Address',
        'deployment_allowed': 'y',
        'attendance_required': 'y',
        'gps_tracking_enabled': 'y',
        'realtime_monitoring_enabled': 'y',
        'geo_fencing_enabled': 'y',
        'workflow_approval_enabled': 'y',
        'document_verification_required': 'y',
        'shift_based_attendance': 'y',
        'max_vehicles': '10',
        'max_drivers': '20',
        'deployment_capacity': '50',
        'required_vehicle_types': 'Truck',
        'operational_capacity': '100',
        'project_manager': 'PM Test',
        'operational_head': 'OH Test',
        'contact_number': '9123456792',
        'operational_email': 'ops@testlogistics.com',
        'submit': 'Create Project',
    }
    post('/projects/create', project_data)
    from app.modules.projects.models import Project
    project = Project.query.filter_by(project_code='TESTPRJ').first()
    print('Project exists:', bool(project), getattr(project, 'id', None))

    # Create subzone
    subzone_data = {
        'company_id': company.id,
        'circle_id': circle.id,
        'client_id': client_obj.id,
        'project_id': project.id,
        'subzone_code': 'TESTSZ',
        'subzone_name': 'Test Subzone',
        'subzone_type': 'Operational Zone',
        'status': 'Active',
        'country': 'India',
        'state': 'Uttar Pradesh',
        'city': 'Lucknow',
        'pincode': '226001',
        'full_address': 'Subzone Address',
        'latitude': '26.8467',
        'longitude': '80.9462',
        'geo_fencing_enabled': 'y',
        'allowed_radius': '500',
        'attendance_radius': '250',
        'gps_validation': 'y',
        'restricted_movement_detection': 'y',
        'max_vehicles': '20',
        'max_drivers': '30',
        'shift_operations_enabled': 'y',
        'attendance_required': 'y',
        'deployment_allowed': 'y',
        'realtime_tracking_enabled': 'y',
        'workflow_approval_enabled': 'y',
        'incident_reporting_enabled': 'y',
        'vehicle_capacity': '80',
        'driver_capacity': '90',
        'parking_capacity': '40',
        'operational_capacity': '100',
        'submit': 'Save Subzone',
    }
    post('/subzones/create', subzone_data)
    from app.modules.subzones.models import Subzone
    subzone = Subzone.query.filter_by(subzone_code='TESTSZ').first()
    print('Subzone exists:', bool(subzone), getattr(subzone, 'id', None))

    # Create driver profile with auto-creation
    driver_username = 'autodriver1'
    driver_data = {
        'identifier': driver_username,
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
        'driving_license_file': (io.BytesIO(b"dummy DL content"), "license.pdf"),
        'aadhaar_file': (io.BytesIO(b"dummy Aadhaar content"), "aadhaar.pdf"),
        'pan_file': (io.BytesIO(b"dummy PAN content"), "pan.pdf"),
        'document_type': 'Driving License',
        'submit': 'Create Driver Profile',
    }
    resp = post('/drivers/create', driver_data)
    html = resp.data.decode('utf-8')
    if "invalid" in html or "alert" in html:
        print("--- DIAGNOSTICS: HTML ERROR LOG ---")
        for line in html.split('\n'):
            if "invalid-feedback" in line or "alert-danger" in line or "<li>" in line:
                print(line.strip())
    driver_user = User.query.filter_by(username=driver_username).first()
    print('Driver user exists:', bool(driver_user), getattr(driver_user, 'email', None))
    from app.modules.drivers.models import DriverProfile
    dp = DriverProfile.query.filter_by(user_id=driver_user.id).first() if driver_user else None
    print('Driver profile exists:', bool(dp), getattr(dp, 'id', None))

    # Create vehicle
    vehicle_data = {
        'company_id': company.id,
        'circle_id': circle.id,
        'client_id': client_obj.id,
        'project_id': project.id,
        'subzone_id': subzone.id,
        'vehicle_number': 'UP32AB1234',
        'vehicle_type': 'Truck',
        'vehicle_category': 'Owned',
        'vehicle_brand': 'Tata',
        'vehicle_model': 'Ace',
        'manufacturing_year': str(datetime.date.today().year),
        'chassis_number': 'CHASSIS123',
        'engine_number': 'ENGINE123',
        'owner_name': 'Owner Name',
        'owner_phone': '9123456794',
        'vendor_name': 'Vendor',
        'vendor_contact': '9123456795',
        'gps_enabled': 'y',
        'realtime_tracking_enabled': 'y',
        'deployment_allowed': 'y',
        'attendance_linked': 'y',
        'fuel_tracking_enabled': 'y',
        'geo_fencing_enabled': 'y',
        'incident_monitoring_enabled': 'y',
        'maintenance_tracking_enabled': 'y',
        'load_capacity': '1000',
        'passenger_capacity': '2',
        'fuel_capacity': '45',
        'operational_capacity': '500',
        'status': 'Available',
        'insurance_status': 'Valid',
        'fitness_status': 'Valid',
        'permit_status': 'Valid',
        'puc_status': 'Valid',
        'verification_status': 'Valid',
        'assigned_driver': driver_user.id,
        'current_deployment': '',
        'submit': 'Save Vehicle',
    }
    post('/vehicles/create', vehicle_data)
    from app.modules.vehicles.models import Vehicle
    vehicle = Vehicle.query.filter_by(vehicle_number='UP32AB1234').first()
    print('Vehicle exists:', bool(vehicle), getattr(vehicle, 'id', None), 'status', getattr(vehicle, 'status', None))

    # Create deployment
    deployment_data = {
        'vehicle_id': vehicle.id,
        'driver_id': driver_user.id,
        'project_id': project.id,
        'subzone_id': subzone.id,
        'deployment_type': 'Standard',
        'route_name': 'Route A',
        'pickup_location': 'Warehouse',
        'dropoff_location': 'Customer Site',
        'vehicle_fitness_verified': 'y',
        'driver_license_verified': 'y',
        'insurance_verified': 'y',
        'safety_checklist_completed': 'y',
        'special_instructions': 'Handle carefully',
        'notes': 'Test deployment',
        'submit': 'Create Deployment',
    }
    post('/deployments/create', deployment_data)
    from app.modules.deployments.models import VehicleDeployment
    deployment = VehicleDeployment.query.filter_by(vehicle_id=vehicle.id).first()
    print('Deployment exists:', bool(deployment), getattr(deployment, 'id', None), 'approval_status', getattr(deployment, 'approval_status', None))
