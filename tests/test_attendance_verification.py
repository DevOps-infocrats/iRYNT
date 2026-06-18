import os
import io
import pytest
from app import create_app, db
from app.modules.auth.models import User, Role
from app.modules.drivers.models import DriverProfile, DriverAttendance
from app.modules.attendance.verification_helpers import decode_base64_image, validate_verification_image

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

def test_decode_base64_image():
    # Valid small PNG base64 representation
    base64_png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    file_storage = decode_base64_image(base64_png, "test_selfie.png")
    assert file_storage is not None
    assert file_storage.filename == "test_selfie.png"
    assert file_storage.content_type == "image/png"
    
    # Run validation
    validate_verification_image(file_storage)

def test_invalid_verification_image():
    # Invalid extension
    from werkzeug.datastructures import FileStorage
    file_storage = FileStorage(stream=io.BytesIO(b"content"), filename="hack.exe", content_type="application/octet-stream")
    with pytest.raises(ValueError, match="Only JPG, JPEG, PNG, and WEBP images are allowed"):
        validate_verification_image(file_storage)

def test_rbac_verification_image(app, client):
    # 1. Setup driver and admin users, and attendance record
    with app.app_context():
        role_driver = Role.query.filter_by(name='Driver').first()
        if not role_driver:
            role_driver = Role(name='Driver')
            db.session.add(role_driver)
            
        role_admin = Role.query.filter_by(name='Super Admin').first()
        if not role_admin:
            role_admin = Role(name='Super Admin')
            db.session.add(role_admin)
            
        db.session.commit()
        
        driver_user = User(username='driver_test', email='driver@test.com')
        driver_user.set_password('pass123')
        driver_user.role_id = role_driver.id
        db.session.add(driver_user)
        db.session.commit()
        driver_user.roles.append(role_driver)
        db.session.commit()
        
        admin_user = User(username='admin_test', email='admin@test.com')
        admin_user.set_password('pass123')
        admin_user.role_id = role_admin.id
        db.session.add(admin_user)
        db.session.commit()
        admin_user.roles.append(role_admin)
        db.session.commit()
        
        profile = DriverProfile(user_id=driver_user.id, active=True)
        db.session.add(profile)
        db.session.commit()
        
        import datetime
        attendance = DriverAttendance(
            driver_id=profile.id,
            date=datetime.date.today(),
            selfie_storage_path="test_dir/selfie.jpg",
            dashboard_storage_path="test_dir/dash.jpg"
        )
        db.session.add(attendance)
        db.session.commit()
        
        driver_user_id = driver_user.id
        admin_user_id = admin_user.id
        attendance_id = attendance.id

    # 2. Driver logs in and gets own verification image -> 404
    with app.test_client() as client_driver:
        with client_driver.session_transaction() as sess:
            sess['_user_id'] = driver_user_id
        resp = client_driver.get(f'/attendance/verification-image/{attendance_id}/selfie')
        assert resp.status_code == 404

    # 3. Create another driver user
    with app.app_context():
        role_driver = Role.query.filter_by(name='Driver').first()
        other_driver = User(username='other_driver', email='other@test.com')
        other_driver.set_password('pass123')
        other_driver.role_id = role_driver.id
        db.session.add(other_driver)
        db.session.commit()
        other_driver.roles.append(role_driver)
        db.session.commit()
        other_driver_id = other_driver.id

    # 4. Other driver logs in and accesses first driver's image -> 403 Forbidden
    with app.test_client() as client_other:
        with client_other.session_transaction() as sess:
            sess['_user_id'] = other_driver_id
        resp = client_other.get(f'/attendance/verification-image/{attendance_id}/selfie')
        assert resp.status_code == 403

    # 5. Admin logs in and accesses first driver's image -> 404
    with app.test_client() as client_admin:
        with client_admin.session_transaction() as sess:
            sess['_user_id'] = admin_user_id
        resp = client_admin.get(f'/attendance/verification-image/{attendance_id}/selfie')
        assert resp.status_code == 404


def test_attendance_odometer_marking(app):
    from app.modules.attendance.services import AttendanceService
    from app.modules.drivers.models import DriverProfile, DriverAttendance
    from app.modules.auth.models import User, Role
    from unittest.mock import patch

    with app.app_context():
        role_driver = Role.query.filter_by(name='Driver').first()
        if not role_driver:
            role_driver = Role(name='Driver')
            db.session.add(role_driver)
        db.session.commit()

        driver_user = User(username='driver_odo_test', email='driver_odo@test.com')
        driver_user.set_password('pass123')
        driver_user.role_id = role_driver.id
        db.session.add(driver_user)
        db.session.commit()
        driver_user.roles.append(role_driver)
        db.session.commit()

        profile = DriverProfile(user_id=driver_user.id, active=True)
        db.session.add(profile)
        db.session.commit()

        service = AttendanceService()

        with patch.object(service.geo_service, 'validate_attendance_location') as mock_val:
            mock_val.return_value = ({'accuracy': 10.0, 'geo_verified': True, 'geo_status': 'GEO_VERIFIED'}, None)

            # Check-in with start odometer
            attendance, error = service.mark_attendance(
                driver_profile_id=profile.id,
                action='check_in',
                location_payload={'latitude': '12.9716', 'longitude': '77.5946', 'accuracy': '10.0'},
                actor_id=driver_user.id,
                odometer=10050.5
            )
            assert error is None
            assert attendance is not None
            assert attendance.start_odometer == 10050.5
            assert attendance.end_odometer is None

            # Check-out with end odometer
            attendance, error = service.mark_attendance(
                driver_profile_id=profile.id,
                action='check_out',
                location_payload={'latitude': '12.9716', 'longitude': '77.5946', 'accuracy': '10.0'},
                actor_id=driver_user.id,
                odometer=10200.8
            )
            assert error is None
            assert attendance is not None
            assert attendance.start_odometer == 10050.5
            assert attendance.end_odometer == 10200.8


def test_helper_attendance_marking(app):
    from app.modules.attendance.services import AttendanceService
    from app.modules.drivers.models import DriverProfile, DriverAttendance
    from app.modules.auth.models import User, Role
    from app.modules.deployments.models import VehicleDeployment
    from unittest.mock import patch
    import datetime

    with app.app_context():
        role_helper = Role.query.filter_by(name='Helper').first()
        if not role_helper:
            role_helper = Role(name='Helper')
            db.session.add(role_helper)
        db.session.commit()

        helper_user = User(username='helper_test', email='helper@test.com')
        helper_user.set_password('pass123')
        helper_user.role_id = role_helper.id
        db.session.add(helper_user)
        db.session.commit()
        helper_user.roles.append(role_helper)
        db.session.commit()

        profile = DriverProfile(user_id=helper_user.id, active=True)
        db.session.add(profile)
        db.session.commit()

        service = AttendanceService()

        with patch.object(service.geo_service, 'validate_attendance_location') as mock_val:
            mock_val.return_value = ({'accuracy': 10.0, 'geo_verified': True, 'geo_status': 'GEO_VERIFIED'}, None)

            # Check-in helper (selfie provided, odometer skipped)
            attendance, error = service.mark_attendance(
                driver_profile_id=profile.id,
                action='check_in',
                location_payload={'latitude': '12.9716', 'longitude': '77.5946', 'accuracy': '10.0'},
                actor_id=helper_user.id,
                selfie_path="helper_selfies/selfie1.jpg"
            )
            assert error is None
            assert attendance is not None
            assert attendance.selfie_storage_path == "helper_selfies/selfie1.jpg"
            assert attendance.start_odometer is None


def test_helper_user_creation_immediate_attendance_marking(app):
    from app.modules.users.services import UserService
    from app.modules.attendance.services import AttendanceService
    from app.modules.companies.models import Company
    from app.modules.circles.models import Circle
    from app.modules.clients.models import Client
    from app.modules.projects.models import Project
    from app.modules.subzones.models import Subzone
    from app.modules.auth.models import User, Role
    from app.modules.drivers.models import DriverProfile
    import datetime

    with app.app_context():
        # 1. Setup Role
        role_helper = Role.query.filter_by(name='Helper').first()
        if not role_helper:
            role_helper = Role(name='Helper')
            db.session.add(role_helper)
        db.session.commit()

        # 2. Setup Company, Circle, Client, Project, Subzone
        company = Company(
            company_name='Test Company Helpers Ltd',
            company_code='TCHL1',
            country_id='IN',
            state_id='KA',
            city_id='BLR',
            pincode='560001'
        )
        db.session.add(company)
        db.session.commit()

        circle = Circle(
            company_id=company.id,
            circle_code='TCIRC1',
            circle_name='Test Circle Helper'
        )
        db.session.add(circle)
        db.session.commit()

        client = Client(
            company_id=company.id,
            circle_id=circle.id,
            client_code='TCLI1',
            client_name='Test Client Helper'
        )
        db.session.add(client)
        db.session.commit()

        project = Project(
            company_id=company.id,
            circle_id=circle.id,
            client_id=client.id,
            project_code='TPROJ1',
            project_name='Test Project Helper',
            project_type='Standard',
            start_date=datetime.date.today()
        )
        db.session.add(project)
        db.session.commit()

        subzone = Subzone(
            company_id=company.id,
            circle_id=circle.id,
            client_id=client.id,
            project_id=project.id,
            subzone_code='TSUBZ1',
            subzone_name='Test Subzone Helper',
            subzone_type='Standard',
            latitude='12.9716',
            longitude='77.5946',
            geo_fencing_enabled=True,
            allowed_radius=500
        )
        db.session.add(subzone)
        db.session.commit()

        # 3. Create helper user via UserService
        user_service = UserService()
        helper_payload = {
            'username': 'helper_sync_test',
            'email': 'helper_sync@test.com',
            'phone': '9999999999',
            'password': 'Password@123',
            'company_id': company.id,
            'circle_id': circle.id,
            'role_id': role_helper.id,
            'is_active': True,
            'is_verified': True,
        }
        
        user = user_service.create_user(helper_payload)
        assert user is not None
        assert user.primary_role.name == 'Helper'

        # 4. Verify DriverProfile was automatically created and synchronized
        profile = DriverProfile.query.filter_by(user_id=user.id).first()
        assert profile is not None
        assert profile.circle_id == circle.id
        assert profile.client_id == client.id
        assert profile.project_id == project.id
        assert profile.subzone_id == subzone.id

        # 5. Verify the helper can immediately mark attendance (using profile subzone, without active deployment)
        attendance_service = AttendanceService()
        attendance, error = attendance_service.mark_attendance(
            driver_profile_id=profile.id,
            action='check_in',
            location_payload={'latitude': '12.9716', 'longitude': '77.5946', 'accuracy': '10.0'},
            actor_id=user.id,
            selfie_path="helper_selfies/sync_selfie.jpg"
        )
        assert error is None
        assert attendance is not None
        assert attendance.status == 'Present'
        assert attendance.selfie_storage_path == "helper_selfies/sync_selfie.jpg"
        assert attendance.geo_verified is True
        assert attendance.geo_status == 'GEO_VERIFIED'


def test_helper_attendance_marking_deployed(app):
    from app.modules.users.services import UserService
    from app.modules.attendance.services import AttendanceService
    from app.modules.companies.models import Company
    from app.modules.circles.models import Circle
    from app.modules.clients.models import Client
    from app.modules.projects.models import Project
    from app.modules.subzones.models import Subzone
    from app.modules.auth.models import User, Role
    from app.modules.drivers.models import DriverProfile
    from app.modules.deployments.models import VehicleDeployment
    from app.modules.vehicles.models import Vehicle
    from app.modules.approvals.models import ApprovalRequest
    from app.modules.notifications.models import Notification
    import datetime

    with app.app_context():
        # Setup helper role & Circle KAM role
        role_helper = Role.query.filter_by(name='Helper').first()
        if not role_helper:
            role_helper = Role(name='Helper')
            db.session.add(role_helper)
        
        role_kam = Role.query.filter_by(name='Circle KAM').first()
        if not role_kam:
            role_kam = Role(name='Circle KAM')
            db.session.add(role_kam)
        db.session.commit()

        # Company A (Home)
        company_a = Company(
            company_name='Company A',
            company_code='COMPA',
            country_id='IN',
            state_id='KA',
            city_id='BLR',
            pincode='560001'
        )
        db.session.add(company_a)
        
        # Company B (Deployed)
        company_b = Company(
            company_name='Company B',
            company_code='COMPB',
            country_id='IN',
            state_id='KA',
            city_id='BLR',
            pincode='560001'
        )
        db.session.add(company_b)
        db.session.commit()

        # Circle A (Home)
        circle_a = Circle(company_id=company_a.id, circle_code='CIRCA', circle_name='Circle A')
        db.session.add(circle_a)

        # Circle B (Deployed)
        circle_b = Circle(company_id=company_b.id, circle_code='CIRCB', circle_name='Circle B')
        db.session.add(circle_b)
        db.session.commit()

        # Circle KAM user for Circle B
        kam_user = User(username='kam_b', email='kam_b@test.com')
        kam_user.set_password('kam123')
        kam_user.company_id = company_b.id
        kam_user.circle_id = circle_b.id
        kam_user.role_id = role_kam.id
        db.session.add(kam_user)
        db.session.commit()
        kam_user.roles.append(role_kam)
        db.session.commit()

        # Setup Client, Project, Subzone under Company B / Circle B
        client_b = Client(company_id=company_b.id, circle_id=circle_b.id, client_code='CLIB', client_name='Client B')
        db.session.add(client_b)
        db.session.commit()

        project_b = Project(
            company_id=company_b.id,
            circle_id=circle_b.id,
            client_id=client_b.id,
            project_code='PROJB',
            project_name='Project B',
            project_type='Standard',
            start_date=datetime.date.today()
        )
        db.session.add(project_b)
        db.session.commit()

        subzone_b = Subzone(
            company_id=company_b.id,
            circle_id=circle_b.id,
            client_id=client_b.id,
            project_id=project_b.id,
            subzone_code='SUBZONEB',
            subzone_name='Subzone B',
            subzone_type='Standard',
            latitude='13.0000',
            longitude='77.6000',
            geo_fencing_enabled=True,
            allowed_radius=100
        )
        db.session.add(subzone_b)
        db.session.commit()

        # Create helper user under Company A / Circle A
        user_service = UserService()
        user = user_service.create_user({
            'username': 'helper_deployed_test',
            'email': 'helper_dep@test.com',
            'phone': '9876543210',
            'password': 'Password@123',
            'company_id': company_a.id,
            'circle_id': circle_a.id,
            'role_id': role_helper.id,
            'is_active': True,
            'is_verified': True,
        })

        # Setup active deployment for the helper under Project B / Subzone B
        vehicle = Vehicle(
            company_id=company_b.id,
            circle_id=circle_b.id,
            client_id=client_b.id,
            project_id=project_b.id,
            subzone_id=subzone_b.id,
            vehicle_number='KA-01-HE-1234',
            vehicle_type='E-Rickshaw',
            vehicle_category='Standard',
            vehicle_brand='TVS',
            vehicle_model='King',
            status='Available'
        )
        db.session.add(vehicle)
        db.session.commit()

        deployment = VehicleDeployment(
            vehicle_id=vehicle.id,
            driver_id=user.id,
            project_id=project_b.id,
            subzone_id=subzone_b.id,
            status='Active',
            approval_status='Approved',
            actual_start=datetime.datetime.utcnow()
        )
        db.session.add(deployment)
        db.session.commit()

        # Mark attendance OUTSIDE Geofence B (Latitude 14.0000, Longitude 78.0000)
        profile = DriverProfile.query.filter_by(user_id=user.id).first()
        attendance_service = AttendanceService()
        attendance, error = attendance_service.mark_attendance(
            driver_profile_id=profile.id,
            action='check_in',
            location_payload={'latitude': '14.0000', 'longitude': '78.0000', 'accuracy': '10.0'},
            actor_id=user.id,
            selfie_path="helper_selfies/dep_selfie.jpg"
        )
        assert error is None
        assert attendance is not None
        assert attendance.geo_status == 'OUTSIDE_GEOFENCE'

        # Verify ApprovalRequest has been created under Company B and Circle B (where they are deployed!)
        app_req = ApprovalRequest.query.filter_by(entity_type='driver_attendance', entity_id=attendance.id).first()
        assert app_req is not None
        assert app_req.company_id == company_b.id
        assert app_req.circle_id == circle_b.id
        assert app_req.assigned_approver_id == kam_user.id

        # Verify Notification generated for Circle KAM has company_id and circle_id set to Company B / Circle B
        kam_notif = Notification.query.filter_by(user_id=kam_user.id).order_by(Notification.created_at.desc()).first()
        assert kam_notif is not None
        assert kam_notif.company_id == company_b.id
        assert kam_notif.circle_id == circle_b.id

        # Verify the helper shows up in the live attendance list for Company B and Circle B
        drivers, total = attendance_service.list_live_attendance(
            filters={'company_id': company_b.id, 'circle_id': circle_b.id},
            page=1,
            per_page=10
        )
        assert total == 1
        assert drivers[0]['id'] == user.id

