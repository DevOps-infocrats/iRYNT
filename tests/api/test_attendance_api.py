import pytest
from app import create_app, db
from app.modules.auth.models import User, Role
from app.modules.drivers.models import DriverProfile, DriverVehicleAssignment
from app.modules.companies.models import Company
from app.modules.circles.models import Circle
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.subzones.models import Subzone
from app.modules.vehicles.models import Vehicle
from app.modules.deployments.models import VehicleDeployment
from flask_jwt_extended import create_access_token
import datetime

@pytest.fixture
def app():
    app = create_app('testing')
    app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_attendance_endpoints_authentication(app, client):
    # Test that requesting without authentication yields 401
    resp = client.post('/api/v1/attendance/check-in', json={})
    assert resp.status_code == 401

    resp = client.post('/api/v1/attendance/check-out', json={})
    assert resp.status_code == 401

    resp = client.post('/api/v1/attendance/gps/sync', json={})
    assert resp.status_code == 401

def test_attendance_endpoints_authorization(app, client):
    # Test that a user without attendance.mark permission gets 403
    with app.app_context():
        role_no_perm = Role.query.filter_by(name='NoPerm').first()
        if not role_no_perm:
            role_no_perm = Role(name='NoPerm')
            db.session.add(role_no_perm)
            db.session.commit()
            
        user = User(username='noperm_user', email='noperm@test.com')
        user.set_password('Password@123')
        user.role_id = role_no_perm.id
        db.session.add(user)
        db.session.commit()
        user.roles.append(role_no_perm)
        db.session.commit()
        
        # Build token with no permissions
        claims = {
            'role': 'NoPerm',
            'permissions': [],
            'username': user.username
        }
        token = create_access_token(identity=user.id, additional_claims=claims)
        headers = {'Authorization': f'Bearer {token}'}
        
    resp = client.post('/api/v1/attendance/check-in', json={}, headers=headers)
    assert resp.status_code == 403

def test_driver_checkin_checkout_success(app, client):
    with app.app_context():
        # Setup helper & driver roles
        role_driver = Role.query.filter_by(name='Driver').first()
        if not role_driver:
            role_driver = Role(name='Driver')
            db.session.add(role_driver)
        db.session.commit()

        # Seed minimal database objects
        company = Company(company_name='Test Company', company_code='TCO', country_id='IN', state_id='KA', city_id='BLR', pincode='560001')
        db.session.add(company)
        db.session.commit()

        circle = Circle(company_id=company.id, circle_code='TCIRC', circle_name='Test Circle')
        db.session.add(circle)
        db.session.commit()

        client_obj = Client(company_id=company.id, circle_id=circle.id, client_code='TCLI', client_name='Test Client')
        db.session.add(client_obj)
        db.session.commit()

        project = Project(company_id=company.id, circle_id=circle.id, client_id=client_obj.id, project_code='TPROJ', project_name='Test Project', project_type='Standard', start_date=datetime.date.today())
        db.session.add(project)
        db.session.commit()

        subzone = Subzone(company_id=company.id, circle_id=circle.id, client_id=client_obj.id, project_id=project.id, subzone_code='TSUB', subzone_name='Test Subzone', subzone_type='Standard', latitude='13.0000', longitude='77.6000', geo_fencing_enabled=False)
        db.session.add(subzone)
        db.session.commit()

        user = User(username='driver_api_user', email='driver_api@test.com', company_id=company.id, circle_id=circle.id)
        user.set_password('Password@123')
        user.role_id = role_driver.id
        db.session.add(user)
        db.session.commit()
        user.roles.append(role_driver)
        db.session.commit()

        profile = DriverProfile(user_id=user.id, active=True, circle_id=circle.id, project_id=project.id, subzone_id=subzone.id, client_id=client_obj.id)
        db.session.add(profile)
        db.session.commit()

        vehicle = Vehicle(company_id=company.id, circle_id=circle.id, client_id=client_obj.id, project_id=project.id, subzone_id=subzone.id, vehicle_number='KA-01-AB-1234', vehicle_type='E-Rickshaw', vehicle_category='Standard', vehicle_brand='TVS', vehicle_model='King', status='Available')
        db.session.add(vehicle)
        db.session.commit()

        deployment = VehicleDeployment(vehicle_id=vehicle.id, driver_id=user.id, project_id=project.id, subzone_id=subzone.id, status='Active', approval_status='Approved', actual_start=datetime.datetime.utcnow())
        db.session.add(deployment)
        db.session.commit()

        assignment = DriverVehicleAssignment(driver_id=profile.id, vehicle_id=vehicle.id, status='Active')
        db.session.add(assignment)
        db.session.commit()

        claims = {
            'role': 'Driver',
            'permissions': ['attendance.mark'],
            'username': user.username
        }
        token = create_access_token(identity=user.id, additional_claims=claims)
        headers = {'Authorization': f'Bearer {token}'}
        
        driver_profile_id = profile.id

    # 1. Test check-in missing odometer reading for driver
    payload = {
        'driver_profile_id': driver_profile_id,
        'latitude': 13.0000,
        'longitude': 77.6000,
        'accuracy': 10.0
    }
    resp = client.post('/api/v1/attendance/check-in', json=payload, headers=headers)
    assert resp.status_code == 400
    assert 'Odometer reading is required' in resp.json['message']

    # 2. Test successful check-in with odometer
    payload['odometer'] = 1500.0
    resp = client.post('/api/v1/attendance/check-in', json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json['success'] is True
    assert resp.json['data']['status'] == 'Present'

    # 3. Test check-out missing odometer
    payload_out = {
        'driver_profile_id': driver_profile_id,
        'latitude': 13.0000,
        'longitude': 77.6000,
        'accuracy': 10.0
    }
    resp = client.post('/api/v1/attendance/check-out', json=payload_out, headers=headers)
    assert resp.status_code == 400

    # 4. Test successful check-out
    payload_out['odometer'] = 1550.0
    resp = client.post('/api/v1/attendance/check-out', json=payload_out, headers=headers)
    assert resp.status_code == 200
    assert resp.json['success'] is True
    assert resp.json['data']['check_out'] is not None

def test_helper_checkin_success(app, client):
    with app.app_context():
        # Setup helper role
        role_helper = Role.query.filter_by(name='Helper').first()
        if not role_helper:
            role_helper = Role(name='Helper')
            db.session.add(role_helper)
        db.session.commit()

        # Seed minimal database objects
        company = Company(company_name='Test Company H', company_code='TCOH', country_id='IN', state_id='KA', city_id='BLR', pincode='560001')
        db.session.add(company)
        db.session.commit()

        circle = Circle(company_id=company.id, circle_code='TCIRCH', circle_name='Test Circle H')
        db.session.add(circle)
        db.session.commit()

        client_obj = Client(company_id=company.id, circle_id=circle.id, client_code='TCLIH', client_name='Test Client H')
        db.session.add(client_obj)
        db.session.commit()

        project = Project(company_id=company.id, circle_id=circle.id, client_id=client_obj.id, project_code='TPROJH', project_name='Test Project H', project_type='Standard', start_date=datetime.date.today())
        db.session.add(project)
        db.session.commit()

        subzone = Subzone(company_id=company.id, circle_id=circle.id, client_id=client_obj.id, project_id=project.id, subzone_code='TSUBH', subzone_name='Test Subzone H', subzone_type='Standard', latitude='13.0000', longitude='77.6000', geo_fencing_enabled=False)
        db.session.add(subzone)
        db.session.commit()

        user = User(username='helper_api_user', email='helper_api@test.com', company_id=company.id, circle_id=circle.id)
        user.set_password('Password@123')
        user.role_id = role_helper.id
        db.session.add(user)
        db.session.commit()
        user.roles.append(role_helper)
        db.session.commit()

        profile = DriverProfile(user_id=user.id, active=True, circle_id=circle.id, project_id=project.id, subzone_id=subzone.id, client_id=client_obj.id)
        db.session.add(profile)
        db.session.commit()

        claims = {
            'role': 'Helper',
            'permissions': ['attendance.mark'],
            'username': user.username
        }
        token = create_access_token(identity=user.id, additional_claims=claims)
        headers = {'Authorization': f'Bearer {token}'}
        
        driver_profile_id = profile.id

    # 1. Test check-in missing selfie for Helper
    payload = {
        'driver_profile_id': driver_profile_id,
        'latitude': 13.0000,
        'longitude': 77.6000,
        'accuracy': 10.0
    }
    resp = client.post('/api/v1/attendance/check-in', json=payload, headers=headers)
    assert resp.status_code == 400
    assert 'selfie is required' in resp.json['message']

    # 2. Test successful check-in with selfie data
    payload['selfie_data'] = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    resp = client.post('/api/v1/attendance/check-in', json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json['success'] is True

def test_gps_sync_success(app, client):
    with app.app_context():
        # Setup driver role
        role_driver = Role.query.filter_by(name='Driver').first()
        if not role_driver:
            role_driver = Role(name='Driver')
            db.session.add(role_driver)
        db.session.commit()

        # Seed minimal database objects
        company = Company(company_name='Test Company G', company_code='TCOG', country_id='IN', state_id='KA', city_id='BLR', pincode='560001')
        db.session.add(company)
        db.session.commit()

        circle = Circle(company_id=company.id, circle_code='TCIRCG', circle_name='Test Circle G')
        db.session.add(circle)
        db.session.commit()

        client_obj = Client(company_id=company.id, circle_id=circle.id, client_code='TCLIG', client_name='Test Client G')
        db.session.add(client_obj)
        db.session.commit()

        project = Project(company_id=company.id, circle_id=circle.id, client_id=client_obj.id, project_code='TPROJG', project_name='Test Project G', project_type='Standard', start_date=datetime.date.today())
        db.session.add(project)
        db.session.commit()

        subzone = Subzone(company_id=company.id, circle_id=circle.id, client_id=client_obj.id, project_id=project.id, subzone_code='TSUBG', subzone_name='Test Subzone G', subzone_type='Standard', latitude='13.0000', longitude='77.6000', geo_fencing_enabled=False)
        db.session.add(subzone)
        db.session.commit()

        user = User(username='gps_driver_user', email='gps_driver@test.com', company_id=company.id, circle_id=circle.id)
        user.set_password('Password@123')
        user.role_id = role_driver.id
        db.session.add(user)
        db.session.commit()
        user.roles.append(role_driver)
        db.session.commit()

        vehicle = Vehicle(company_id=company.id, circle_id=circle.id, client_id=client_obj.id, project_id=project.id, subzone_id=subzone.id, vehicle_number='KA-01-XY-9876', vehicle_type='E-Rickshaw', vehicle_category='Standard', vehicle_brand='TVS', vehicle_model='King', status='Available')
        db.session.add(vehicle)
        db.session.commit()

        deployment = VehicleDeployment(vehicle_id=vehicle.id, driver_id=user.id, project_id=project.id, subzone_id=subzone.id, status='Active', approval_status='Approved', actual_start=datetime.datetime.utcnow())
        db.session.add(deployment)
        db.session.commit()

        claims = {
            'role': 'Driver',
            'permissions': ['attendance.mark'],
            'username': user.username
        }
        token = create_access_token(identity=user.id, additional_claims=claims)
        headers = {'Authorization': f'Bearer {token}'}
        
        deployment_id = deployment.id
        vehicle_id = vehicle.id

    # Sync coordinates
    payload = {
        'deployment_id': deployment_id,
        'coordinates': [
            {
                'latitude': 12.9716,
                'longitude': 77.5946,
                'timestamp': '2026-06-22T10:00:00Z',
                'speed': 25.0,
                'accuracy': 5.0
            },
            {
                'latitude': 12.9718,
                'longitude': 77.5948,
                'timestamp': '2026-06-22T10:05:00Z',
                'speed': 30.0,
                'accuracy': 4.5
            }
        ]
    }

    resp = client.post('/api/v1/attendance/gps/sync', json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json['success'] is True

    # Verify database updates
    with app.app_context():
        v = Vehicle.query.get(vehicle_id)
        d = VehicleDeployment.query.get(deployment_id)
        assert v.current_location == "12.9718,77.5948"
        assert d.current_location == "12.9718,77.5948"
        assert v.last_gps_ping is not None
