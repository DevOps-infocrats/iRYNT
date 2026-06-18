"""One-off smoke test: create a deployment via service and print result.

Run with: .venv\Scripts\python.exe scripts\smoke_test_deployment.py
"""
import sys
import os
# Ensure repo root is on sys.path so `import app` works when run from scripts/
sys.path.insert(0, os.getcwd())

from app import create_app

app = create_app('development')

with app.app_context():
    from app.modules.deployments.services import DeploymentService
    from app.modules.vehicles.models import Vehicle
    from app.modules.auth.models import User
    from app.extensions import db

    svc = DeploymentService()

    vehicle = Vehicle.query.filter_by(status='Available').first()
    user = User.query.filter_by(is_active=True).first()

    if not vehicle:
        print('No available vehicle found — cannot run smoke test.')
        sys.exit(2)

    if not user:
        print('No active user found — cannot run smoke test.')
        sys.exit(2)

    payload = {
        'vehicle_id': vehicle.id,
        'driver_id': vehicle.assigned_driver_id if getattr(vehicle, 'assigned_driver_id', None) else None,
        'project_id': vehicle.project_id,
        'subzone_id': vehicle.subzone_id,
        'deployment_type': 'Standard',
        'route_name': 'Smoke Test Route',
        'pickup_location': 'Test Pickup',
        'dropoff_location': 'Test Dropoff',
        'vehicle_fitness_verified': True,
        'driver_license_verified': True,
        'insurance_verified': True,
        'safety_checklist_completed': True,
        'special_instructions': 'Smoke test',
        'notes': 'Created by smoke_test_deployment.py',
    }

    deployment, error = svc.create_deployment(payload, user.id)

    if error:
        print('Create deployment failed:', error)
        sys.exit(1)

    print('Deployment created:')
    print('  id:', deployment.id)
    print('  status:', deployment.status)
    print('  approval_status:', deployment.approval_status)
    print('  approved_by:', getattr(deployment, 'approved_by', None))
    print('  approval_timestamp:', getattr(deployment, 'approval_timestamp', None))
    sys.exit(0)
