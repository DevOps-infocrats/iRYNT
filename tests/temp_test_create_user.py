from app import create_app
from app.extensions import db
from app.modules.auth.models import User

app = create_app('testing')
with app.app_context():
    # Ensure we have a test admin user and login the test client
    from app.modules.users.services import UserService
    user_service = UserService()
    admin_role = None
    from app.modules.auth.models import Role
    admin_role = Role.query.filter_by(name='Super Admin').first()
    admin_payload = {
        'username': 'testadmin',
        'email': 'testadmin@example.local',
        'password': 'Admin@12345',
        'is_active': True,
        'is_verified': True,
        'role_id': admin_role.id if admin_role else None,
    }
    admin = User.query.filter_by(username='testadmin').first()
    if not admin:
        admin = user_service.create_user(admin_payload)

    client = app.test_client()
    # set login in session for flask-login
    with client.session_transaction() as sess:
        sess['_user_id'] = admin.id
    data = {
        'identifier': 'autodriver1',
        'submit': 'Create Driver Profile'
    }
    resp = client.post('/drivers/create', data=data, follow_redirects=True)
    print('POST /drivers/create status:', resp.status_code)
    print('Response body (truncated):')
    print(resp.data.decode('utf-8')[:1000])
    # Check whether a user was created with username or email
    user = User.query.filter_by(username='autodriver1').first()
    if user:
        print('User created:', user.username, user.email, 'id=', user.id)
    else:
        # maybe username was modified to ensure uniqueness
        user_like = User.query.filter(User.email.ilike('%autodriver1%')).first()
        print('User found by email-like:', bool(user_like))
    # List driver profiles count
    from app.modules.drivers.models import DriverProfile
    profiles = DriverProfile.query.all()
    print('Driver profiles count:', len(profiles))
