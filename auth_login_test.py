import re

from app import create_app
from app.modules.auth.models import User

app = create_app('development')
with app.app_context():
    client = app.test_client()
    response = client.get('/login')
    html = response.data.decode('utf-8')
    match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', html)
    csrf_token = match.group(1) if match else None
    print('csrf_token_found', csrf_token is not None)

    post = client.post(
        '/login',
        data={
            'login_identifier': 'superadmin',
            'password': 'Admin@321',
            'remember_me': 'y',
            'csrf_token': csrf_token,
        },
        follow_redirects=False,
    )
    print('login_status', post.status_code)
    print('login_location', post.headers.get('Location'))
    print('login_body', post.data.decode('utf-8')[:400])

    user = User.query.filter_by(username='superadmin').first()
    print('user_exists', bool(user), user.email if user else None)
