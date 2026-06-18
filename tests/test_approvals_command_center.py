import os
import io
import pytest
from datetime import datetime, timezone, timedelta
from app import create_app, db
from app.modules.auth.models import User, Role, Permission
from app.modules.approvals.models import ApprovalRequest, ApprovalHistory, ApprovalComment

@pytest.fixture
def app():
    app = create_app('testing')
    app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for easier form postings in tests
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def create_role_and_user(username, email, role_name, company_id=None, circle_id=None):
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        role = Role(name=role_name)
        db.session.add(role)
        db.session.commit()
        
    # Grant necessary permissions for approvals to the role
    for perm_name in ['workflows.view', 'workflows.approve', 'workflows.manage', 'approval.view', 'approval.approve', 'approval.reject', 'approval.escalate']:
        perm = Permission.query.filter_by(name=perm_name).first()
        if not perm:
            perm = Permission(name=perm_name)
            db.session.add(perm)
            db.session.commit()
        if perm not in role.permissions:
            role.permissions.append(perm)
            
    db.session.commit()

    user = User(username=username, email=email, company_id=company_id, circle_id=circle_id)
    user.set_password('pass123')
    user.role_id = role.id
    db.session.add(user)
    db.session.commit()
    user.roles.append(role)
    db.session.commit()
    return user

def test_approvals_command_center_flows(app, client):
    with app.app_context():
        # Create roles and users
        driver_user = create_role_and_user('driver_bob', 'bob@test.com', 'Driver')
        circle_kam = create_role_and_user('kam_circle', 'circle@test.com', 'Circle KAM', circle_id='circle_east')
        pmo_user = create_role_and_user('pmo_john', 'pmo@test.com', 'PMO')
        corporate_kam = create_role_and_user('kam_corp', 'corp@test.com', 'Corporate Admin', company_id='vil_corp')
        super_admin = create_role_and_user('admin_super', 'super@test.com', 'Super Admin')

        # Create approval requests
        # 1. Attendance correction requested by Driver, assigned to Circle KAM, circle_east
        req1 = ApprovalRequest(
            approval_type='attendance_correction',
            module_name='attendance',
            entity_type='DriverAttendance',
            entity_id='att_123',
            request_title='Attendance correction Bob',
            requested_by_id=driver_user.id,
            assigned_approver_id=circle_kam.id,
            circle_id='circle_east',
            priority='Medium',
            approval_status='Pending',
            sla_due_at=datetime.now(timezone.utc) + timedelta(hours=5)
        )
        db.session.add(req1)

        # 2. License verification, requested by Driver, assigned to Circle KAM, circle_east, critical & SLA breached
        req2 = ApprovalRequest(
            approval_type='license_verification',
            module_name='compliance',
            entity_type='DriverLicense',
            entity_id='lic_123',
            request_title='Bob License Renewal',
            requested_by_id=driver_user.id,
            assigned_approver_id=circle_kam.id,
            circle_id='circle_east',
            priority='Critical',
            approval_status='Pending',
            sla_due_at=datetime.now(timezone.utc) - timedelta(hours=2)
        )
        db.session.add(req2)

        # 3. Project approval, PMO type, assigned to PMO
        req3 = ApprovalRequest(
            approval_type='project_approval',
            module_name='projects',
            entity_type='Project',
            entity_id='proj_456',
            request_title='New Highway Circle Circle',
            requested_by_id=circle_kam.id,
            assigned_approver_id=pmo_user.id,
            priority='High',
            approval_status='Pending'
        )
        db.session.add(req3)

        # 4. Another attendance correction, circle_west, not visible to Circle KAM of circle_east
        req4 = ApprovalRequest(
            approval_type='attendance_correction',
            module_name='attendance',
            entity_type='DriverAttendance',
            entity_id='att_456',
            request_title='Attendance correction Alice',
            requested_by_id=super_admin.id,
            circle_id='circle_west',
            priority='Low',
            approval_status='Pending'
        )
        db.session.add(req4)

        db.session.commit()

        # Capture IDs
        req1_id = req1.id
        req2_id = req2.id
        req3_id = req3.id
        req4_id = req4.id
        driver_id = driver_user.id
        circle_kam_id = circle_kam.id
        pmo_id = pmo_user.id
        corp_id = corporate_kam.id
        super_id = super_admin.id

    # Test Visibility Scopes
    # A. Driver Bob can only see own requests (req1, req2)
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['_user_id'] = driver_id
        
        # 1. Main index - check query result counts
        resp = c.get('/pending-approvals/?category=all')
        assert resp.status_code == 200
        # Check that Bob can read own title
        assert b"Attendance correction Bob" in resp.data
        assert b"Bob License Renewal" in resp.data
        # Bob cannot see PMO or other circle's attendance
        assert b"New Highway Circle Circle" not in resp.data
        assert b"Attendance correction Alice" not in resp.data

        # 2. AJAX Detail endpoint -> allowed for own
        resp = c.get(f'/pending-approvals/ajax/detail/{req1_id}')
        assert resp.status_code == 200
        # AJAX Detail endpoint -> unauthorized for other's
        resp = c.get(f'/pending-approvals/ajax/detail/{req3_id}')
        assert resp.status_code == 403

    # B. Circle KAM can see attendance/compliance/escalations inside circle_east (req1, req2)
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['_user_id'] = circle_kam_id
        
        resp = c.get('/pending-approvals/?category=all')
        assert resp.status_code == 200
        assert b"Attendance correction Bob" in resp.data
        assert b"Bob License Renewal" in resp.data
        # Cannot see project approval (PMO type) or circle_west attendance
        assert b"New Highway Circle Circle" not in resp.data
        assert b"Attendance correction Alice" not in resp.data

    # C. PMO can see project approvals (req3)
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['_user_id'] = pmo_id
        
        resp = c.get('/pending-approvals/?category=all')
        assert resp.status_code == 200
        assert b"New Highway Circle Circle" in resp.data
        # PMO cannot see attendance
        assert b"Attendance correction Bob" not in resp.data

    # D. Super Admin has unrestricted access
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['_user_id'] = super_id
        
        resp = c.get('/pending-approvals/?category=all')
        assert resp.status_code == 200
        assert b"Attendance correction Bob" in resp.data
        assert b"Bob License Renewal" in resp.data
        assert b"New Highway Circle Circle" in resp.data
        assert b"Attendance correction Alice" in resp.data

    # Test Category Filters and Stats under Super Admin
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['_user_id'] = super_id
        
        # Attendance category (should contain req1, req4)
        resp = c.get('/pending-approvals/?category=attendance')
        assert b"Attendance correction Bob" in resp.data
        assert b"Attendance correction Alice" in resp.data
        assert b"New Highway Circle Circle" not in resp.data

        # Critical category (should contain req2)
        resp = c.get('/pending-approvals/?category=critical')
        assert b"Bob License Renewal" in resp.data
        assert b"Attendance correction Bob" not in resp.data

        # Overdue category (should contain req2 which is SLA breached)
        resp = c.get('/pending-approvals/?category=overdue')
        assert b"Bob License Renewal" in resp.data
        assert b"Attendance correction Bob" not in resp.data

        # AJAX Stats
        resp = c.get('/pending-approvals/ajax/stats')
        data = resp.json
        assert data['total_pending'] == 4
        assert data['critical_pending'] == 1
        assert data['sla_breached'] == 1

    # Test Action Redirection via next parameter
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['_user_id'] = super_id

        # POST approve request with next pointing to index
        next_target = '/pending-approvals/?category=attendance'
        resp = c.post(f'/pending-approvals/approve/{req1_id}', data={
            'remarks': 'Approved Bob',
            'next': next_target
        })
        # Assert redirect to next parameter target
        assert resp.status_code == 302
        assert resp.location.endswith(next_target)

        # Confirm status update
        with app.app_context():
            req = ApprovalRequest.query.get(req1_id)
            assert req.approval_status == 'Approved'

    # Test Reassign Endpoint
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['_user_id'] = super_id

        next_target = '/pending-approvals/?category=all'
        resp = c.post(f'/pending-approvals/reassign/{req2_id}', data={
            'approver_id': pmo_id,
            'next': next_target
        })
        assert resp.status_code == 302
        assert resp.location.endswith(next_target)

        with app.app_context():
            req = ApprovalRequest.query.get(req2_id)
            assert req.assigned_approver_id == pmo_id
