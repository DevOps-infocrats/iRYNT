import pytest
from app import create_app, db
from app.modules.auth.models import User, Role
from app.core.sidebar import build_sidebar_menu
from flask_login import current_user

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

def test_dashboard_access_and_sidebar_filtering(app, client):
    with app.app_context():
        # Setup roles
        role_driver = Role.query.filter_by(name='Driver').first()
        if not role_driver:
            role_driver = Role(name='Driver')
            db.session.add(role_driver)
            
        role_helper = Role.query.filter_by(name='Helper').first()
        if not role_helper:
            role_helper = Role(name='Helper')
            db.session.add(role_helper)

        role_admin = Role.query.filter_by(name='Super Admin').first()
        if not role_admin:
            role_admin = Role(name='Super Admin')
            db.session.add(role_admin)
            
        db.session.commit()
        
        # Setup Driver User
        driver_user = User(username='driver_dash_test', email='driver_dash@test.com')
        driver_user.set_password('pass123')
        driver_user.role_id = role_driver.id
        db.session.add(driver_user)
        db.session.commit()
        driver_user.roles.append(role_driver)
        
        # Setup Helper User
        helper_user = User(username='helper_dash_test', email='helper_dash@test.com')
        helper_user.set_password('pass123')
        helper_user.role_id = role_helper.id
        db.session.add(helper_user)
        db.session.commit()
        helper_user.roles.append(role_helper)
        
        # Setup Admin User
        admin_user = User(username='admin_dash_test', email='admin_dash@test.com')
        admin_user.set_password('pass123')
        admin_user.role_id = role_admin.id
        db.session.add(admin_user)
        db.session.commit()
        admin_user.roles.append(role_admin)
        db.session.commit()
        
        driver_id = driver_user.id
        helper_id = helper_user.id
        admin_id = admin_user.id

    # 1. Driver login and access to dashboard -> should redirect to /attendance/live
    with app.test_client() as client_driver:
        with client_driver.session_transaction() as sess:
            sess['_user_id'] = driver_id
        
        # Make a request to the dashboard
        resp = client_driver.get('/dashboard')
        assert resp.status_code == 302
        assert '/attendance/live' in resp.headers.get('Location')

        # Verify driver sidebar menu does not have dashboard section
        # Inside request context so build_sidebar_menu works
        with client_driver.session_transaction():
            resp_side = client_driver.get('/attendance/live') # triggers context
            # We can check sidebar menu inside request context
            with app.test_request_context():
                # Manually log in user inside request context to test sidebar
                from flask_login import login_user
                user_obj = User.query.get(driver_id)
                login_user(user_obj)
                sidebar = build_sidebar_menu()
                # Ensure 'dashboard' key is not in sidebar sections
                section_keys = [section['key'] for section in sidebar]
                assert 'dashboard' not in section_keys

    # 2. Helper login and access to dashboard -> should redirect to /attendance/live
    with app.test_client() as client_helper:
        with client_helper.session_transaction() as sess:
            sess['_user_id'] = helper_id
        
        resp = client_helper.get('/dashboard')
        assert resp.status_code == 302
        assert '/attendance/live' in resp.headers.get('Location')

        # Verify helper sidebar menu does not have dashboard section
        with client_helper.session_transaction():
            resp_side = client_helper.get('/attendance/live')
            with app.test_request_context():
                from flask_login import login_user
                user_obj = User.query.get(helper_id)
                login_user(user_obj)
                sidebar = build_sidebar_menu()
                section_keys = [section['key'] for section in sidebar]
                assert 'dashboard' not in section_keys

    # 3. Admin login and access to dashboard -> should load successfully (200 status or 302 to login if not logged in, but here they are logged in)
    with app.test_client() as client_admin:
        with client_admin.session_transaction() as sess:
            sess['_user_id'] = admin_id
        
        resp = client_admin.get('/dashboard')
        # Admin has dashboard access, so they either get 200 or direct template rendering
        assert resp.status_code == 200 or resp.status_code == 302 and '/attendance/live' not in resp.headers.get('Location')
        
        with client_admin.session_transaction():
            resp_side = client_admin.get('/dashboard')
            with app.test_request_context():
                from flask_login import login_user
                user_obj = User.query.get(admin_id)
                login_user(user_obj)
                sidebar = build_sidebar_menu()
                section_keys = [section['key'] for section in sidebar]
                assert 'dashboard' in section_keys
