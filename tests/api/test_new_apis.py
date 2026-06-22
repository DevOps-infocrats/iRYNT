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
from app.modules.deployments.models import VehicleDeployment, HelperAssignment
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

def test_endpoints_authentication(app, client):
    # Test that requesting without authentication yields 401
    resp = client.get('/api/v1/deployments/current')
    assert resp.status_code == 401

    resp = client.get('/api/v1/vehicles/current')
    assert resp.status_code == 401

def test_endpoints_authorization(app, client):
    # Test that a user without permission deployments.view or attendance.mark gets 403
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
        
    resp = client.get('/api/v1/deployments/current', headers=headers)
    assert resp.status_code == 403

    resp = client.get('/api/v1/vehicles/current', headers=headers)
    assert resp.status_code == 403

def test_driver_deployment_and_vehicle_endpoints(app, client):
    with app.app_context():
        # Setup driver role
        role_driver = Role.query.filter_by(name='Driver').first()
        if not role_driver:
            role_driver = Role(name='Driver')
            db.session.add(role_driver)
        db.session.commit()

        # Seed database objects
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

        vehicle = Vehicle(
            company_id=company.id, circle_id=circle.id, client_id=client_obj.id, project_id=project.id, subzone_id=subzone.id,
            vehicle_number='KA-01-AB-1234', vehicle_type='E-Rickshaw', vehicle_category='Standard', vehicle_brand='TVS', vehicle_model='King',
            status='Available', vehicle_running=12000.0, insurance_expiry=datetime.date(2027, 12, 31), fitness_expiry=datetime.date(2027, 12, 31)
        )
        db.session.add(vehicle)
        db.session.commit()

        deployment = VehicleDeployment(
            vehicle_id=vehicle.id, driver_id=user.id, project_id=project.id, subzone_id=subzone.id,
            status='Active', approval_status='Approved', actual_start=datetime.datetime.utcnow()
        )
        db.session.add(deployment)
        db.session.commit()

        claims = {
            'role': 'Driver',
            'permissions': ['attendance.mark'],
            'username': user.username
        }
        token = create_access_token(identity=user.id, additional_claims=claims)
        headers = {'Authorization': f'Bearer {token}'}

    # Test deployments endpoint
    resp = client.get('/api/v1/deployments/current', headers=headers)
    assert resp.status_code == 200
    assert resp.json['success'] is True
    data = resp.json['data']
    assert data['project'] == 'Test Project'
    assert data['circle'] == 'Test Circle'
    assert data['subzone'] == 'Test Subzone'
    assert data['vehicle_number'] == 'KA-01-AB-1234'
    assert data['status'] == 'Active'

    # Test vehicles endpoint
    resp = client.get('/api/v1/vehicles/current', headers=headers)
    assert resp.status_code == 200
    assert resp.json['success'] is True
    data = resp.json['data']
    assert data['vehicle_number'] == 'KA-01-AB-1234'
    assert data['vehicle_type'] == 'E-Rickshaw'
    assert data['odometer'] == 12000.0
    assert data['insurance_expiry'] == '2027-12-31'
    assert data['fitness_expiry'] == '2027-12-31'

def test_helper_deployment_and_vehicle_endpoints(app, client):
    with app.app_context():
        # Setup helper role
        role_helper = Role.query.filter_by(name='Helper').first()
        if not role_helper:
            role_helper = Role(name='Helper')
            db.session.add(role_helper)
        db.session.commit()

        # Seed database objects
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

        vehicle = Vehicle(
            company_id=company.id, circle_id=circle.id, client_id=client_obj.id, project_id=project.id, subzone_id=subzone.id,
            vehicle_number='KA-01-AB-9999', vehicle_type='E-Rickshaw', vehicle_category='Standard', vehicle_brand='TVS', vehicle_model='King',
            status='Available', vehicle_running=5000.0, insurance_expiry=datetime.date(2027, 12, 31), fitness_expiry=datetime.date(2027, 12, 31)
        )
        db.session.add(vehicle)
        db.session.commit()

        helper_assignment = HelperAssignment(
            helper_id=user.id, circle_id=circle.id, project_id=project.id, subzone_id=subzone.id,
            assigned_vehicle_id=vehicle.id, status='Active'
        )
        db.session.add(helper_assignment)
        db.session.commit()

        # Let's also create an active deployment for the vehicle (to make it complete)
        deployment = VehicleDeployment(
            vehicle_id=vehicle.id, driver_id=None, project_id=project.id, subzone_id=subzone.id,
            status='Active', approval_status='Approved', actual_start=datetime.datetime.utcnow()
        )
        db.session.add(deployment)
        db.session.commit()

        claims = {
            'role': 'Helper',
            'permissions': ['attendance.mark'],
            'username': user.username
        }
        token = create_access_token(identity=user.id, additional_claims=claims)
        headers = {'Authorization': f'Bearer {token}'}

    # Test deployments endpoint
    resp = client.get('/api/v1/deployments/current', headers=headers)
    assert resp.status_code == 200
    assert resp.json['success'] is True
    data = resp.json['data']
    assert data['project'] == 'Test Project H'
    assert data['circle'] == 'Test Circle H'
    assert data['subzone'] == 'Test Subzone H'
    assert data['vehicle_number'] == 'KA-01-AB-9999'
    assert data['status'] == 'Active'

    # Test vehicles endpoint
    resp = client.get('/api/v1/vehicles/current', headers=headers)
    assert resp.status_code == 200
    assert resp.json['success'] is True
    data = resp.json['data']
    assert data['vehicle_number'] == 'KA-01-AB-9999'
    assert data['vehicle_type'] == 'E-Rickshaw'
    assert data['odometer'] == 5000.0
    assert data['insurance_expiry'] == '2027-12-31'
    assert data['fitness_expiry'] == '2027-12-31'

def test_empty_deployment_and_vehicle_endpoints(app, client):
    with app.app_context():
        role_driver = Role.query.filter_by(name='Driver').first()
        if not role_driver:
            role_driver = Role(name='Driver')
            db.session.add(role_driver)
        db.session.commit()

        user = User(username='driver_empty_user', email='driver_empty@test.com')
        user.set_password('Password@123')
        user.role_id = role_driver.id
        db.session.add(user)
        db.session.commit()
        user.roles.append(role_driver)
        db.session.commit()

        claims = {
            'role': 'Driver',
            'permissions': ['attendance.mark'],
            'username': user.username
        }
        token = create_access_token(identity=user.id, additional_claims=claims)
        headers = {'Authorization': f'Bearer {token}'}

    # Test deployments endpoint with no deployment
    resp = client.get('/api/v1/deployments/current', headers=headers)
    assert resp.status_code == 200
    assert resp.json['success'] is True
    data = resp.json['data']
    assert data['project'] == ""
    assert data['circle'] == ""
    assert data['subzone'] == ""
    assert data['vehicle_number'] == ""
    assert data['status'] == ""

    # Test vehicles endpoint with no vehicle
    resp = client.get('/api/v1/vehicles/current', headers=headers)
    assert resp.status_code == 200
    assert resp.json['success'] is True
    data = resp.json['data']
    assert data['vehicle_number'] == ""
    assert data['vehicle_type'] == ""
    assert data['odometer'] == ""
    assert data['insurance_expiry'] == ""
    assert data['fitness_expiry'] == ""
