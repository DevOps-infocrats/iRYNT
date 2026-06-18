import pytest
from app import create_app, db
from app.modules.auth.models import User, Role
from app.modules.notifications.models import Notification
from app.modules.notifications.helpers import create_notification_safe
from app.infrastructure.repositories.notifications.notifications_repository import NotificationsRepository
from app.delivery.web.routes.notifications_routes import migrate_existing_notifications

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

def test_dynamic_notification_categorization(app):
    with app.app_context():
        # Create a test user
        role_driver = Role.query.filter_by(name='Driver').first() or Role(name='Driver')
        db.session.add(role_driver)
        db.session.commit()

        user = User(username='notif_test_user', email='notif@test.com')
        user.set_password('Password@123')
        user.role_id = role_driver.id
        db.session.add(user)
        db.session.commit()

        # 1. Test Attendance notification creation mapping
        create_notification_safe(user_id=user.id, message="Helper clocked in", module="attendance")
        # 2. Test Deployment notification creation mapping
        create_notification_safe(user_id=user.id, message="Vehicle assigned to driver", module="deployments")
        # 3. Test Approval notification creation mapping
        create_notification_safe(user_id=user.id, message="Odometer override requires approval", module="approvals")
        # 4. Test Escalation notification creation mapping
        create_notification_safe(user_id=user.id, message="SLA escalation warning", module="approvals")
        # 5. Test Expiry notification creation mapping
        create_notification_safe(user_id=user.id, message="Driver license expiring soon", module="documents")
        # 6. Test default System notification
        create_notification_safe(user_id=user.id, message="Welcome to VIL ERP", module="system")

        # Query all notifications and assert types
        notifs = Notification.query.all()
        assert len(notifs) == 6

        attendance_notif = Notification.query.filter_by(module="attendance").first()
        assert attendance_notif.type == "attendance"

        deployment_notif = Notification.query.filter_by(module="deployments").first()
        assert deployment_notif.type == "deployment"

        approval_notif = Notification.query.filter(Notification.module == "approvals", Notification.message.ilike("%approval%")).first()
        assert approval_notif.type == "approval"

        escalation_notif = Notification.query.filter(Notification.module == "approvals", Notification.message.ilike("%escalat%")).first()
        assert escalation_notif.type == "escalation"

        expiry_notif = Notification.query.filter_by(module="documents").first()
        assert expiry_notif.type == "expiry"

        system_notif = Notification.query.filter_by(module="system").first()
        assert system_notif.type == "system"


def test_feed_filtering_and_summary_counts(app):
    with app.app_context():
        user = User(username='notif_filter_user', email='notif_filter@test.com')
        user.set_password('Password@123')
        db.session.add(user)
        db.session.commit()

        # Seed notifications of various categories and priorities
        # 2 Attendance notifications (one read, one unread)
        n1 = Notification(user_id=user.id, type="attendance", module="attendance", message="Clocked in", priority="info", is_read=False)
        n2 = Notification(user_id=user.id, type="attendance", module="attendance", message="Clocked out", priority="info", is_read=True)
        # 1 Critical Deployment alert (unread)
        n3 = Notification(user_id=user.id, type="deployment", module="deployments", message="Deployment failed", priority="Critical", is_read=False)
        # 1 Escalation alert (unread)
        n4 = Notification(user_id=user.id, type="escalation", module="approvals", message="Escalated to CBH", priority="High", is_read=False)
        # 1 Approval alert (read)
        n5 = Notification(user_id=user.id, type="approval", module="approvals", message="Approval request approved", priority="info", is_read=True)

        db.session.add_all([n1, n2, n3, n4, n5])
        db.session.commit()

        # Verify repo listing filter
        feed_attendance = NotificationsRepository.list_for_user(user.id, filters={'type': 'attendance'})
        assert len(feed_attendance['items']) == 2
        assert all(item['type'] == 'attendance' for item in feed_attendance['items'])

        feed_deployment = NotificationsRepository.list_for_user(user.id, filters={'type': 'deployment'})
        assert len(feed_deployment['items']) == 1
        assert feed_deployment['items'][0]['type'] == 'deployment'

        # Verify summary dashboard counters
        summary = feed_attendance['summary']
        assert summary['unread'] == 3  # n1, n3, n4 are unread
        assert summary['critical'] == 1  # n3 is critical
        assert summary['approvals'] == 1  # n5 is approval (total count)
        assert summary['escalations'] == 1  # n4 is escalation (total count)


def test_historical_data_migration(app):
    with app.app_context():
        # Seed legacy notifications (all defaulted to 'system')
        n1 = Notification(type="system", module="attendance", message="Clocked in")
        n2 = Notification(type="system", module="deployments", message="Route started")
        n3 = Notification(type="system", module="approvals", message="Approval needed")
        n4 = Notification(type="system", module="approvals", message="Escalated alert")
        n5 = Notification(type="system", module="documents", message="Insurance expiry")
        n6 = Notification(type="system", module="system", message="Welcome to VIL")

        db.session.add_all([n1, n2, n3, n4, n5, n6])
        db.session.commit()

        # Run migration function
        migrate_existing_notifications()

        # Verify mapping was backfilled correctly
        assert Notification.query.get(n1.id).type == "attendance"
        assert Notification.query.get(n2.id).type == "deployment"
        assert Notification.query.get(n3.id).type == "approval"
        assert Notification.query.get(n4.id).type == "escalation"
        assert Notification.query.get(n5.id).type == "expiry"
        assert Notification.query.get(n6.id).type == "system"


def test_notification_routes_access(app, client):
    with app.app_context():
        # Create a test user with notifications.view permission
        role_admin = Role.query.filter_by(name='Circle Admin').first()
        if not role_admin:
            role_admin = Role(name='Circle Admin')
            db.session.add(role_admin)
        db.session.commit()

        # Ensure permissions seeded or template updated
        from seeds.permissions_seed import seed_predefined_permissions
        seed_predefined_permissions()

        # Associate permissions with Circle Admin
        from seeds.roles_seed import seed_predefined_roles
        seed_predefined_roles()

        user = User(username='route_test_admin', email='route_test@test.com')
        user.set_password('Password@123')
        user.role_id = role_admin.id
        db.session.add(user)
        db.session.commit()
        user.roles.append(role_admin)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = user_id

    # Test accessing specific notification endpoints
    resp_system = client.get('/notifications/system')
    assert resp_system.status_code == 200

    resp_expiry = client.get('/notifications/expiry')
    assert resp_expiry.status_code == 200

    resp_attendance = client.get('/notifications/attendance')
    assert resp_attendance.status_code == 200

    resp_deployment = client.get('/notifications/deployment')
    assert resp_deployment.status_code == 200


def test_odometer_warning_expiry_categorization_and_fallback(app):
    with app.app_context():
        # 1. Test fallback to system-wide when role has no users
        from app.modules.notifications.helpers import create_notifications_for_roles_safe
        create_notifications_for_roles_safe(
            ['Non Existent Role'],
            message="Odometer warning: Vehicle KA01AB1234 reached 140000 km",
            module="vehicles",
            priority="Warning",
            type="expiry"
        )
        
        # Verify it fallback created a system-wide notification with user_id=None and type='expiry'
        system_wide = Notification.query.filter_by(user_id=None).first()
        assert system_wide is not None
        assert system_wide.type == 'expiry'
        assert system_wide.module == 'vehicles'

        # 2. Verify legacy migration for odometer/km/vehicle module alerts
        db.session.delete(system_wide)
        db.session.commit()
        
        legacy_notif = Notification(
            type="system",
            module="vehicles",
            message="140000 KM Warning: Vehicle KA01AB1234 reached threshold",
            user_id=None
        )
        db.session.add(legacy_notif)
        db.session.commit()
        
        from app.delivery.web.routes.notifications_routes import migrate_existing_notifications
        migrate_existing_notifications()
        
        # Verify it got migrated to 'expiry'
        migrated = Notification.query.get(legacy_notif.id)
        assert migrated.type == 'expiry'


def test_admin_scope_and_category_counts(app):
    with app.app_context():
        # Create a Super Admin, a Circle Admin, and a regular driver user
        from app.modules.auth.models import User, Role
        
        role_super = Role.query.filter_by(name='Super Admin').first() or Role(name='Super Admin')
        role_circle_admin = Role.query.filter_by(name='Circle Admin').first() or Role(name='Circle Admin')
        role_driver = Role.query.filter_by(name='Driver').first() or Role(name='Driver')
        
        db.session.add_all([role_super, role_circle_admin, role_driver])
        db.session.commit()
        
        super_user = User(username='super_test', email='super_test@test.com')
        super_user.set_password('pass123')
        super_user.roles.append(role_super)
        
        circle_id_1 = "circle-1"
        circle_id_2 = "circle-2"
        company_id_1 = "company-1"
        
        c_admin = User(username='c_admin_test', email='c_admin_test@test.com', company_id=company_id_1, circle_id=circle_id_1)
        c_admin.set_password('pass123')
        c_admin.roles.append(role_circle_admin)
        
        driver = User(username='driver_test', email='driver_test@test.com', company_id=company_id_1, circle_id=circle_id_1)
        driver.set_password('pass123')
        driver.roles.append(role_driver)
        
        db.session.add_all([super_user, c_admin, driver])
        db.session.commit()
        
        # 1. Create a notification targeted to the driver
        n1 = Notification(
            user_id=driver.id,
            type='attendance',
            module='attendance',
            message='Attendance Marked for driver',
            priority='Medium',
            company_id=company_id_1,
            circle_id=circle_id_1
        )
        # 2. Create an expiry notification targeted to another circle
        n2 = Notification(
            user_id=None,
            type='expiry',
            module='compliance',
            message='Odometer warning in circle 2',
            priority='Warning',
            company_id=company_id_1,
            circle_id=circle_id_2
        )
        
        db.session.add_all([n1, n2])
        db.session.commit()
        
        # Super Admin should see both notifications globally
        feed_super = NotificationsRepository.list_for_user(super_user.id)
        assert len(feed_super['items']) == 2
        
        # Circle Admin (circle-1) should see the driver's attendance notification, but NOT circle-2's warning
        feed_c_admin = NotificationsRepository.list_for_user(c_admin.id)
        assert len(feed_c_admin['items']) == 1
        assert feed_c_admin['items'][0]['id'] == n1.id
        
        # Driver should see only their own notification
        feed_driver = NotificationsRepository.list_for_user(driver.id)
        assert len(feed_driver['items']) == 1
        assert feed_driver['items'][0]['id'] == n1.id
        
        # Test category count filtering in summary_counts_for_user
        # With category='attendance'
        summary_attendance = NotificationsRepository.summary_counts_for_user(super_user.id, filters={'type': 'attendance'})
        assert summary_attendance['unread'] == 1
        
        # With category='expiry'
        summary_expiry = NotificationsRepository.summary_counts_for_user(super_user.id, filters={'type': 'expiry'})
        assert summary_expiry['unread'] == 1

