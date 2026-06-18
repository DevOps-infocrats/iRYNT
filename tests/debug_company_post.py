import os
import sys

sys.path.insert(0, os.getcwd())

from app import create_app
from app.modules.auth.models import User

app = create_app('testing')

with app.app_context():
    admin = User.query.filter_by(username='superadmin').first()
    if not admin:
        raise RuntimeError('superadmin user not found')

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['_user_id'] = admin.id

    company_data = {
        'company_name': 'Test Logistics Ltd',
        'company_code': 'TESTLOG',
        'gst_number': '29ABCDE1234F2Z5',
        'pan_number': 'ABCDE1234F',
        'email': 'info@testlogistics.local',
        'phone': '9123456789',
        'country_id': 'IN',
        'state_id': 'UP',
        'city_id': 'LKO',
        'pincode': '226001',
        'status': 'Active',
        'submit': 'Save Company',
    }

    resp = client.post('/companies/create', data=company_data, follow_redirects=True)
    text = resp.data.decode('utf-8', errors='replace')
    print('status', resp.status_code)
    print('headers', resp.headers)
    print('invalid-feedback count', text.count('invalid-feedback'))
    print('company exists', 'TESTLOG' in text)
    print('form snippet:')
    form_start = text.find('<form')
    form_end = text.find('</form>', form_start)
    if form_start != -1 and form_end != -1:
        print(text[form_start:form_end+7])
    else:
        print('form not found')
    print('full errors:')
    for line in text.splitlines():
        if 'invalid-feedback' in line or 'error' in line.lower() or 'flash' in line.lower():
            print(line)
