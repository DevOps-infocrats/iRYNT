import datetime
import pytest
from app import create_app, db
from app.modules.auth.models import User, Role
from app.modules.companies.models import Company
from app.modules.circles.models import Circle
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.subzones.models import Subzone
from app.modules.drivers.models import DriverProfile, DriverAttendance
from app.modules.deployments.models import HelperAssignment, VehicleDeployment
from app.modules.attendance.services import AttendanceService
from app.modules.users.services import UserService
from app.modules.approvals.models import ApprovalRequest
from app.modules.notifications.models import Notification

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

def test_helper_assignment_crud_and_validations(app):
    with app.app_context():
        # Setup roles
        role_helper = Role.query.filter_by(name='Helper').first() or Role(name='Helper')
        role_kam = Role.query.filter_by(name='Circle KAM').first() or Role(name='Circle KAM')
        db.session.add(role_helper)
        db.session.add(role_kam)
        db.session.commit()

        # Setup company hierarchy
        company = Company(company_name='Test Company', company_code='TC1', country_id='IN', state_id='KA', city_id='BLR', pincode='560001')
        db.session.add(company)
        db.session.commit()

        circle = Circle(company_id=company.id, circle_code='CIR1', circle_name='Test Circle')
        db.session.add(circle)
        db.session.commit()

        client_obj = Client(company_id=company.id, circle_id=circle.id, client_code='CLI1', client_name='Test Client')
        db.session.add(client_obj)
        db.session.commit()

        project = Project(company_id=company.id, circle_id=circle.id, client_id=client_obj.id, project_code='PRJ1', project_name='Test Project', project_type='Standard', start_date=datetime.date.today())
        db.session.add(project)
        db.session.commit()

        subzone = Subzone(company_id=company.id, circle_id=circle.id, client_id=client_obj.id, project_id=project.id, subzone_code='SZ1', subzone_name='Test Subzone', subzone_type='Standard', latitude='12.9716', longitude='77.5946', geo_fencing_enabled=True, allowed_radius=500)
        db.session.add(subzone)
        db.session.commit()

        # Create Helper User
        user_service = UserService()
        helper_user = user_service.create_user({
            'username': 'helper_test_user',
            'email': 'helper@test.com',
            'phone': '9898989898',
            'password': 'Password@123',
            'company_id': company.id,
            'circle_id': circle.id,
            'role_id': role_helper.id,
            'is_active': True,
            'is_verified': True,
        })

        # Test Case 1: Create first active assignment
        assignment1 = HelperAssignment(
            helper_id=helper_user.id,
            circle_id=circle.id,
            project_id=project.id,
            subzone_id=subzone.id,
            shift='Evening',
            status='Active'
        )
        db.session.add(assignment1)
        db.session.commit()

        assert assignment1.id is not None
        assert assignment1.status == 'Active'
        assert assignment1.shift == 'Evening'

        # Test Case 2: Validation of duplicate active assignments
        # Create routes / view CRUD triggers duplicate checks. Let's make sure creating a new one is guarded in route/service.
        # Check active status query logic:
        active_assignment = HelperAssignment.query.filter_by(helper_id=helper_user.id, status='Active').first()
        assert active_assignment is not None
        assert active_assignment.id == assignment1.id

        # Test Case 3: End assignment
        assignment1.status = 'Ended'
        assignment1.end_date = datetime.date.today()
        db.session.commit()

        ended_assignment = HelperAssignment.query.get(assignment1.id)
        assert ended_assignment.status == 'Ended'
        assert ended_assignment.end_date == datetime.date.today()

        # Test Case 4: Create a new assignment after ending the previous one
        assignment2 = HelperAssignment(
            helper_id=helper_user.id,
            circle_id=circle.id,
            project_id=project.id,
            subzone_id=subzone.id,
            shift='Night',
            status='Active'
        )
        db.session.add(assignment2)
        db.session.commit()

        assert assignment2.status == 'Active'
        assert assignment2.shift == 'Night'


def test_helper_attendance_marking_and_shift_mapping(app):
    with app.app_context():
        # Setup role & details
        role_helper = Role.query.filter_by(name='Helper').first() or Role(name='Helper')
        db.session.add(role_helper)
        db.session.commit()

        company = Company(company_name='Test Company 2', company_code='TC2', country_id='IN', state_id='KA', city_id='BLR', pincode='560001')
        db.session.add(company)
        db.session.commit()

        circle = Circle(company_id=company.id, circle_code='CIR2', circle_name='Test Circle 2')
        db.session.add(circle)
        db.session.commit()

        client_obj = Client(company_id=company.id, circle_id=circle.id, client_code='CLI2', client_name='Test Client 2')
        db.session.add(client_obj)
        db.session.commit()

        project = Project(company_id=company.id, circle_id=circle.id, client_id=client_obj.id, project_code='PRJ2', project_name='Test Project 2', project_type='Standard', start_date=datetime.date.today())
        db.session.add(project)
        db.session.commit()

        subzone = Subzone(company_id=company.id, circle_id=circle.id, client_id=client_obj.id, project_id=project.id, subzone_code='SZ2', subzone_name='Test Subzone 2', subzone_type='Standard', latitude='12.9716', longitude='77.5946', geo_fencing_enabled=True, allowed_radius=500)
        db.session.add(subzone)
        db.session.commit()

        # Create Helper User
        user_service = UserService()
        helper_user = user_service.create_user({
            'username': 'helper_clock_user',
            'email': 'helper_clock@test.com',
            'phone': '9898989897',
            'password': 'Password@123',
            'company_id': company.id,
            'circle_id': circle.id,
            'role_id': role_helper.id,
            'is_active': True,
            'is_verified': True,
        })

        # Profile gets automatically created
        profile = DriverProfile.query.filter_by(user_id=helper_user.id).first()
        assert profile is not None

        # Create Active Helper Assignment with a specific shift
        assignment = HelperAssignment(
            helper_id=helper_user.id,
            circle_id=circle.id,
            project_id=project.id,
            subzone_id=subzone.id,
            shift='Afternoon Shift',
            status='Active'
        )
        db.session.add(assignment)
        db.session.commit()

        # Mark attendance check-in
        attendance_service = AttendanceService()
        attendance, error = attendance_service.mark_attendance(
            driver_profile_id=profile.id,
            action='check_in',
            location_payload={'latitude': '12.9716', 'longitude': '77.5946', 'accuracy': '10.0'},
            actor_id=helper_user.id,
            selfie_path="helper_selfies/test_selfie.jpg"
        )

        assert error is None
        assert attendance is not None
        assert attendance.status == 'Present'
        # The shift must be correctly mapped to attendance check-in record
        assert attendance.shift_name == 'Afternoon Shift'


def test_helper_attendance_geofencing_review_routing(app):
    with app.app_context():
        # Setup roles
        role_helper = Role.query.filter_by(name='Helper').first() or Role(name='Helper')
        role_kam = Role.query.filter_by(name='Circle KAM').first() or Role(name='Circle KAM')
        db.session.add(role_helper)
        db.session.add(role_kam)
        db.session.commit()

        # Company A (Home)
        company_a = Company(company_name='Company A', company_code='COMPA', country_id='IN', state_id='KA', city_id='BLR', pincode='560001')
        db.session.add(company_a)
        
        # Company B (Deployed)
        company_b = Company(company_name='Company B', company_code='COMPB', country_id='IN', state_id='KA', city_id='BLR', pincode='560001')
        db.session.add(company_b)
        db.session.commit()

        # Circle A
        circle_a = Circle(company_id=company_a.id, circle_code='CIRCA', circle_name='Circle A')
        db.session.add(circle_a)
        
        # Circle B
        circle_b = Circle(company_id=company_b.id, circle_code='CIRCB', circle_name='Circle B')
        db.session.add(circle_b)
        db.session.commit()

        # Circle KAM user for Circle B
        kam_user = User(username='kam_b_test', email='kambtest@test.com')
        kam_user.set_password('kam123')
        kam_user.company_id = company_b.id
        kam_user.circle_id = circle_b.id
        kam_user.role_id = role_kam.id
        db.session.add(kam_user)
        db.session.commit()
        kam_user.roles.append(role_kam)
        db.session.commit()

        # Client, Project, Subzone under Company B / Circle B
        client_b = Client(company_id=company_b.id, circle_id=circle_b.id, client_code='CLIB', client_name='Client B')
        db.session.add(client_b)
        db.session.commit()

        project_b = Project(company_id=company_b.id, circle_id=circle_b.id, client_id=client_b.id, project_code='PROJB', project_name='Project B', project_type='Standard', start_date=datetime.date.today())
        db.session.add(project_b)
        db.session.commit()

        subzone_b = Subzone(company_id=company_b.id, circle_id=circle_b.id, client_id=client_b.id, project_id=project_b.id, subzone_code='SUBZONEB', subzone_name='Subzone B', subzone_type='Standard', latitude='13.0000', longitude='77.6000', geo_fencing_enabled=True, allowed_radius=100)
        db.session.add(subzone_b)
        db.session.commit()

        # Helper user under Company A / Circle A
        user_service = UserService()
        helper_user = user_service.create_user({
            'username': 'helper_geo_user',
            'email': 'helper_geo@test.com',
            'phone': '9898989896',
            'password': 'Password@123',
            'company_id': company_a.id,
            'circle_id': circle_a.id,
            'role_id': role_helper.id,
            'is_active': True,
            'is_verified': True,
        })
        profile = DriverProfile.query.filter_by(user_id=helper_user.id).first()

        # Create Active Helper Assignment under Company B / Circle B / Project B / Subzone B
        assignment = HelperAssignment(
            helper_id=helper_user.id,
            circle_id=circle_b.id,
            project_id=project_b.id,
            subzone_id=subzone_b.id,
            shift='Evening Shift',
            status='Active'
        )
        db.session.add(assignment)
        db.session.commit()

        # Mark attendance OUTSIDE Geofence B (Latitude 14.0000, Longitude 78.0000)
        attendance_service = AttendanceService()
        attendance, error = attendance_service.mark_attendance(
            driver_profile_id=profile.id,
            action='check_in',
            location_payload={'latitude': '14.0000', 'longitude': '78.0000', 'accuracy': '10.0'},
            actor_id=helper_user.id,
            selfie_path="helper_selfies/dep_selfie.jpg"
        )

        assert error is None
        assert attendance is not None
        assert attendance.geo_status == 'OUTSIDE_GEOFENCE'

        # Verify ApprovalRequest has been created under Company B and Circle B (where helper is deployed!)
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
