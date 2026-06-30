import datetime
from unittest.mock import patch

import pytest

from app import create_app, db
from app.modules.attendance.approval_constants import (
    APPROVAL_STATUS_KAM_APPROVED,
    APPROVAL_STATUS_MIS_APPROVED,
    APPROVAL_STATUS_REJECTED,
    APPROVAL_STATUS_SUBMITTED,
)
from app.modules.attendance.approval_service import AttendanceApprovalService
from app.modules.attendance.services import AttendanceService
from app.modules.auth.models import Role, User
from app.modules.circles.models import Circle
from app.modules.clients.models import Client
from app.modules.companies.models import Company
from app.modules.drivers.models import DriverAttendance, DriverProfile
from app.modules.projects.models import Project
from app.modules.subzones.models import Subzone
from app.modules.vehicles.models import Vehicle
from app.modules.deployments.models import VehicleDeployment


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


def _ensure_role(name):
    role = Role.query.filter_by(name=name).first()
    if not role:
        role = Role(name=name)
        db.session.add(role)
        db.session.commit()
    return role


def _create_user(username, role_name, circle_id=None, company_id=None):
    role = _ensure_role(role_name)
    user = User(username=username, email=f'{username}@test.com', circle_id=circle_id, company_id=company_id)
    user.set_password('Password@123')
    user.role_id = role.id
    db.session.add(user)
    db.session.commit()
    user.roles.append(role)
    db.session.commit()
    return user


def _seed_circle_hierarchy():
    company = Company.query.filter_by(company_code='TCO').first()
    if not company:
        company = Company(
            company_name='Test Co',
            company_code='TCO',
            country_id='IN',
            state_id='KA',
            city_id='BLR',
            pincode='560001',
        )
        db.session.add(company)
        db.session.commit()

    circle_a = Circle.query.filter_by(circle_code='CA').first()
    if not circle_a:
        circle_a = Circle(circle_name='Circle A', circle_code='CA', company_id=company.id)
        db.session.add(circle_a)
        db.session.commit()

    circle_b = Circle.query.filter_by(circle_code='CB').first()
    if not circle_b:
        circle_b = Circle(circle_name='Circle B', circle_code='CB', company_id=company.id)
        db.session.add(circle_b)
        db.session.commit()

    client = Client.query.filter_by(client_code='CLA').first()
    if not client:
        client = Client(
            client_name='Client A',
            client_code='CLA',
            company_id=company.id,
            circle_id=circle_a.id,
        )
        db.session.add(client)
        db.session.commit()

    project = Project.query.filter_by(project_code='PA').first()
    if not project:
        project = Project(
            project_name='Project A',
            project_code='PA',
            project_type='Standard',
            start_date=datetime.date.today(),
            company_id=company.id,
            circle_id=circle_a.id,
            client_id=client.id,
        )
        db.session.add(project)
        db.session.commit()

    subzone = Subzone.query.filter_by(subzone_code='SA').first()
    if not subzone:
        subzone = Subzone(
            subzone_name='Subzone A',
            subzone_code='SA',
            subzone_type='Standard',
            project_id=project.id,
            company_id=company.id,
            circle_id=circle_a.id,
            client_id=client.id,
            latitude='12.9716',
            longitude='77.5946',
            allowed_radius=500,
        )
        db.session.add(subzone)
        db.session.commit()

    vehicle = Vehicle.query.filter_by(vehicle_number='KA01AB1234').first()
    if not vehicle:
        vehicle = Vehicle(
            vehicle_number='KA01AB1234',
            vehicle_type='E-Rickshaw',
            vehicle_category='Standard',
            vehicle_brand='TVS',
            vehicle_model='King',
            company_id=company.id,
            circle_id=circle_a.id,
            client_id=client.id,
            project_id=project.id,
            subzone_id=subzone.id,
        )
        db.session.add(vehicle)
        db.session.commit()

    return company, circle_a, circle_b, project, subzone, vehicle


def _geo_ok(*args, **kwargs):
    return {
        'geo_status': 'GEO_VERIFIED',
        'geo_verified': True,
        'distance_meters': 10,
        'accuracy': 5,
        'deployment': None,
        'subzone': None,
    }, None


@pytest.fixture
def client(app):
    return app.test_client()


@patch('app.modules.attendance.services.AttendanceGeoService.validate_attendance_location', side_effect=_geo_ok)
@patch('app.modules.attendance.services.AttendanceGeoService.apply_geo_result')
@patch('app.modules.attendance.services.AttendanceGeoService.create_review_request_if_needed')
@patch('app.modules.attendance.services.AttendanceGeoService.log_geo_audit')
def test_driver_attendance_submission_sets_submitted(mock_log, mock_review, mock_apply, mock_geo, app):
    with app.app_context():
        company, circle_a, _, project, subzone, vehicle = _seed_circle_hierarchy()
        driver_user = _create_user('driver1', 'Driver', circle_id=circle_a.id, company_id=company.id)
        profile = DriverProfile(user_id=driver_user.id, circle_id=circle_a.id, project_id=project.id, subzone_id=subzone.id)
        db.session.add(profile)
        db.session.commit()

        deployment = VehicleDeployment(
            vehicle_id=vehicle.id,
            driver_id=driver_user.id,
            project_id=project.id,
            subzone_id=subzone.id,
            status='Active',
            approval_status='Approved',
            actual_start=datetime.datetime.utcnow(),
        )
        db.session.add(deployment)
        from app.modules.drivers.models import DriverVehicleAssignment
        db.session.add(DriverVehicleAssignment(driver_id=profile.id, vehicle_id=vehicle.id, status='Active'))
        db.session.commit()

        service = AttendanceService()
        attendance, error = service.mark_attendance(profile.id, 'check_in', location_payload={'latitude': '12.97', 'longitude': '77.59', 'accuracy': '5'})
        assert error is None
        assert attendance.approval_status == APPROVAL_STATUS_SUBMITTED
        assert attendance.status == 'Present'


def test_mis_to_kam_approval_workflow(app):
    with app.app_context():
        company, circle_a, circle_b, project, subzone, vehicle = _seed_circle_hierarchy()
        mis_user = _create_user('mis_a', 'MIS', circle_id=circle_a.id, company_id=company.id)
        kam_user = _create_user('kam_a', 'Circle KAM', circle_id=circle_a.id, company_id=company.id)
        driver_user = _create_user('driver2', 'Driver', circle_id=circle_a.id, company_id=company.id)
        profile = DriverProfile(user_id=driver_user.id, driver_code='DRV002', circle_id=circle_a.id, project_id=project.id, subzone_id=subzone.id)
        db.session.add(profile)
        db.session.commit()

        attendance = DriverAttendance(
            driver_id=profile.id,
            date=datetime.date.today(),
            check_in=datetime.datetime.utcnow(),
            status='Present',
            approval_status=APPROVAL_STATUS_SUBMITTED,
            selfie_storage_path='selfie.jpg',
            dashboard_storage_path='dash.jpg',
            start_odometer=1000,
        )
        db.session.add(attendance)
        db.session.commit()

        approval_service = AttendanceApprovalService()
        updated, error = approval_service.mis_approve(
            attendance,
            mis_user,
            {
                'seatbelt_verified': True,
                'selfie_verified': True,
                'dashboard_verified': True,
                'odometer_verified': True,
            },
            remarks='Looks good',
        )
        assert error is None
        assert updated.approval_status == APPROVAL_STATUS_MIS_APPROVED
        assert updated.seatbelt_verified is True

        updated, error = approval_service.kam_approve(attendance, kam_user, remarks='Final OK')
        assert error is None
        assert updated.approval_status == APPROVAL_STATUS_KAM_APPROVED


def test_attendance_images_are_stored_in_db_and_served(app):
    with app.app_context():
        company, circle_a, _, project, subzone, _ = _seed_circle_hierarchy()
        driver_user = _create_user('driver4', 'Driver', circle_id=circle_a.id, company_id=company.id)
        profile = DriverProfile(user_id=driver_user.id, driver_code='DRV004', circle_id=circle_a.id, project_id=project.id, subzone_id=subzone.id)
        db.session.add(profile)
        db.session.commit()

        attendance = DriverAttendance(
            driver_id=profile.id,
            date=datetime.date.today(),
            check_in=datetime.datetime.utcnow(),
            status='Present',
            approval_status=APPROVAL_STATUS_SUBMITTED,
        )
        db.session.add(attendance)
        db.session.commit()

        attendance.selfie_image_data = 'data:image/jpeg;base64,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'
        attendance.dashboard_image_data = 'data:image/jpeg;base64,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'
        db.session.commit()

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['_user_id'] = driver_user.id

            response = client.get(f'/attendance/verification-image/{attendance.id}/selfie')
            assert response.status_code == 200
            assert response.mimetype.startswith('image/')
            assert b'JFIF' in response.data or b'PNG' in response.data
    with app.app_context():
        company, circle_a, _, project, subzone, _ = _seed_circle_hierarchy()
        superadmin = User.query.filter_by(username='superadmin').first()
        assert superadmin is not None

        driver_user = _create_user('driver3', 'Driver', circle_id=circle_a.id, company_id=company.id)
        profile = DriverProfile(user_id=driver_user.id, driver_code='DRV003', circle_id=circle_a.id, project_id=project.id, subzone_id=subzone.id)
        db.session.add(profile)
        db.session.commit()

        attendance = DriverAttendance(
            driver_id=profile.id,
            date=datetime.date.today(),
            check_in=datetime.datetime.utcnow(),
            status='Present',
            approval_status=APPROVAL_STATUS_MIS_APPROVED,
            selfie_storage_path='selfie.jpg',
            dashboard_storage_path='dash.jpg',
            mis_verified_at=datetime.datetime.utcnow(),
        )
        db.session.add(attendance)
        db.session.commit()

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['_user_id'] = superadmin.id

            response = client.get('/attendance/kam-approvals')
            assert response.status_code == 200
            assert b'/attendance/verification-image/' in response.data
            assert b'Selfie' in response.data or b'Dashboard' in response.data


def test_helper_mis_verification_checklist(app):
    with app.app_context():
        company, circle_a, _, project, subzone, _ = _seed_circle_hierarchy()
        mis_user = _create_user('mis_helper', 'MIS', circle_id=circle_a.id, company_id=company.id)
        helper_user = _create_user('helper1', 'Helper', circle_id=circle_a.id, company_id=company.id)
        profile = DriverProfile(user_id=helper_user.id, circle_id=circle_a.id, project_id=project.id, subzone_id=subzone.id)
        db.session.add(profile)
        db.session.commit()

        attendance = DriverAttendance(
            driver_id=profile.id,
            date=datetime.date.today(),
            check_in=datetime.datetime.utcnow(),
            status='Present',
            approval_status=APPROVAL_STATUS_SUBMITTED,
            selfie_storage_path='selfie.jpg',
        )
        db.session.add(attendance)
        db.session.commit()

        approval_service = AttendanceApprovalService()
        updated, error = approval_service.mis_approve(
            attendance,
            mis_user,
            {
                'helmet_verified': True,
                'safety_shoes_verified': True,
                'safety_jacket_verified': True,
                'id_card_verified': True,
            },
        )
        assert error is None
        assert updated.helmet_verified is True
        assert updated.approval_status == APPROVAL_STATUS_MIS_APPROVED


def test_cross_circle_mis_approval_blocked(app):
    with app.app_context():
        company, circle_a, circle_b, project, subzone, _ = _seed_circle_hierarchy()
        mis_b = _create_user('mis_b', 'MIS', circle_id=circle_b.id, company_id=company.id)
        driver_user = _create_user('driver3', 'Driver', circle_id=circle_a.id, company_id=company.id)
        profile = DriverProfile(user_id=driver_user.id, circle_id=circle_a.id, project_id=project.id, subzone_id=subzone.id)
        db.session.add(profile)
        db.session.commit()

        attendance = DriverAttendance(
            driver_id=profile.id,
            date=datetime.date.today(),
            check_in=datetime.datetime.utcnow(),
            status='Present',
            approval_status=APPROVAL_STATUS_SUBMITTED,
        )
        db.session.add(attendance)
        db.session.commit()

        approval_service = AttendanceApprovalService()
        _, error = approval_service.mis_approve(attendance, mis_b, {'selfie_verified': True})
        assert error == 'Cross-circle approval is not allowed.'


def test_mis_resubmission_clears_checkin(app):
    with app.app_context():
        company, circle_a, _, project, subzone, _ = _seed_circle_hierarchy()
        mis_user = _create_user('mis_resubmit', 'MIS', circle_id=circle_a.id, company_id=company.id)
        driver_user = _create_user('driver4', 'Driver', circle_id=circle_a.id, company_id=company.id)
        profile = DriverProfile(user_id=driver_user.id, circle_id=circle_a.id, project_id=project.id, subzone_id=subzone.id)
        db.session.add(profile)
        db.session.commit()

        attendance = DriverAttendance(
            driver_id=profile.id,
            date=datetime.date.today(),
            check_in=datetime.datetime.utcnow(),
            status='Present',
            approval_status=APPROVAL_STATUS_SUBMITTED,
        )
        db.session.add(attendance)
        db.session.commit()

        approval_service = AttendanceApprovalService()
        _, error = approval_service.mis_request_resubmission(attendance, mis_user, remarks='Blurry selfie')
        assert error is None
        assert attendance.approval_status == APPROVAL_STATUS_REJECTED
        assert attendance.check_in is None
        assert '[RESUBMISSION REQUESTED]' in attendance.mis_remarks


def test_kam_rejection(app):
    with app.app_context():
        company, circle_a, _, project, subzone, _ = _seed_circle_hierarchy()
        kam_user = _create_user('kam_reject', 'Circle KAM', circle_id=circle_a.id, company_id=company.id)
        driver_user = _create_user('driver5', 'Driver', circle_id=circle_a.id, company_id=company.id)
        profile = DriverProfile(user_id=driver_user.id, circle_id=circle_a.id, project_id=project.id, subzone_id=subzone.id)
        db.session.add(profile)
        db.session.commit()

        attendance = DriverAttendance(
            driver_id=profile.id,
            date=datetime.date.today(),
            check_in=datetime.datetime.utcnow(),
            status='Present',
            approval_status=APPROVAL_STATUS_MIS_APPROVED,
        )
        db.session.add(attendance)
        db.session.commit()

        approval_service = AttendanceApprovalService()
        _, error = approval_service.kam_reject(attendance, kam_user, remarks='Incomplete verification')
        assert error is None
        assert attendance.approval_status == APPROVAL_STATUS_REJECTED


def test_api_response_includes_approval_status_label(app, client):
    with app.app_context():
        from flask_jwt_extended import create_access_token

        company, circle_a, _, project, subzone, vehicle = _seed_circle_hierarchy()
        role_driver = _ensure_role('Driver')
        driver_user = _create_user('api_driver', 'Driver', circle_id=circle_a.id, company_id=company.id)
        profile = DriverProfile(user_id=driver_user.id, circle_id=circle_a.id, project_id=project.id, subzone_id=subzone.id)
        db.session.add(profile)
        db.session.commit()

        attendance = DriverAttendance(
            driver_id=profile.id,
            date=datetime.date.today(),
            check_in=datetime.datetime.utcnow(),
            status='Present',
            approval_status=APPROVAL_STATUS_SUBMITTED,
        )
        db.session.add(attendance)
        db.session.commit()

        claims = {'role': 'Driver', 'permissions': ['attendance.mark'], 'username': driver_user.username}
        token = create_access_token(identity=driver_user.id, additional_claims=claims)
        headers = {'Authorization': f'Bearer {token}'}

    resp = client.get('/api/v1/attendance/history', headers=headers)
    assert resp.status_code == 200
    payload = resp.get_json()
    record = payload['data']['records'][0]
    assert record['approval_status'] == APPROVAL_STATUS_SUBMITTED
    assert 'MIS Approval' in record['approval_status_label']


def test_kam_approval_syncs_workflow_request(app):
    with app.app_context():
        company, circle_a, _, project, subzone, _ = _seed_circle_hierarchy()
        mis_user = _create_user('mis_wf', 'MIS', circle_id=circle_a.id, company_id=company.id)
        kam_user = _create_user('kam_wf', 'Circle KAM', circle_id=circle_a.id, company_id=company.id)
        driver_user = _create_user('driver_wf', 'Driver', circle_id=circle_a.id, company_id=company.id)
        profile = DriverProfile(user_id=driver_user.id, circle_id=circle_a.id, project_id=project.id, subzone_id=subzone.id)
        db.session.add(profile)
        db.session.commit()

        from app.modules.approvals.models import ApprovalRequest

        attendance = DriverAttendance(
            driver_id=profile.id,
            date=datetime.date.today(),
            check_in=datetime.datetime.utcnow(),
            status='Present',
            approval_status=APPROVAL_STATUS_SUBMITTED,
        )
        db.session.add(attendance)
        db.session.commit()

        approval_service = AttendanceApprovalService()
        approval_service.sync_workflow_on_submission(attendance, profile, driver_user.id)
        db.session.commit()

        workflow = ApprovalRequest.query.filter_by(
            entity_type='driver_attendance',
            entity_id=attendance.id,
            approval_type='attendance_verification',
        ).first()
        assert workflow is not None
        assert workflow.approval_status == 'Pending'
        assert workflow.circle_id == circle_a.id

        approval_service.mis_approve(attendance, mis_user, {'selfie_verified': True})
        db.session.refresh(workflow)
        assert workflow.approval_status == 'Under Review'

        approval_service.kam_approve(attendance, kam_user, remarks='Final approval')
        db.session.refresh(workflow)
        assert workflow.approval_status == 'Approved'
        assert attendance.approval_status == APPROVAL_STATUS_KAM_APPROVED


def test_historical_attendance_null_approval_status_valid(app):
    with app.app_context():
        company, circle_a, _, project, subzone, _ = _seed_circle_hierarchy()
        driver_user = _create_user('legacy_driver', 'Driver', circle_id=circle_a.id, company_id=company.id)
        profile = DriverProfile(user_id=driver_user.id, circle_id=circle_a.id, project_id=project.id, subzone_id=subzone.id)
        db.session.add(profile)
        db.session.commit()

        attendance = DriverAttendance(
            driver_id=profile.id,
            date=datetime.date.today() - datetime.timedelta(days=30),
            check_in=datetime.datetime.utcnow() - datetime.timedelta(days=30),
            status='Present',
            approval_status=None,
        )
        db.session.add(attendance)
        db.session.commit()

        records, total = AttendanceService().list_attendance_history({'driver_id': profile.id}, 1, 10)
        assert total == 1
        assert records[0].approval_status is None
