"""Smoke test: perform an operational driver assignment end-to-end.
Run: .venv\Scripts\python.exe scripts\smoke_test_assign.py
"""
import sys
import os
sys.path.insert(0, os.getcwd())
from app import create_app

app = create_app('development')

with app.app_context():
    from app.modules.deployments.services import DeploymentService
    from app.services.compliance.assignment_validation_service import AssignmentValidationService
    from app.modules.vehicles.models import Vehicle
    from app.modules.auth.models import User
    from app.modules.drivers.models import DriverVehicleAssignment
    from app.extensions import db
    from datetime import datetime, timezone

    svc = DeploymentService()
    validator = AssignmentValidationService()

    vehicle = Vehicle.query.filter_by(status='Available').first()
    if not vehicle:
        print('No available vehicle found. Aborting.')
        sys.exit(2)

    # find a driver with a driver_profile
    driver = User.query.filter(User.driver_profile != None).first()
    if not driver:
        print('No driver with profile found. Aborting.')
        sys.exit(2)

    print('Selected vehicle:', vehicle.vehicle_number, 'driver:', driver.username)

    result = validator.validate_assignment(driver_id=driver.id, vehicle_id=vehicle.id, project_id=vehicle.project_id, subzone_id=vehicle.subzone_id)
    print('Validation result:', result)

    if not result['is_valid']:
        print('Assignment blocked:', result['blocking_issues'])
        # record failed assignment audit
        profile = getattr(driver, 'driver_profile', None)
        drv_profile_id = profile.id if profile else None
        assign = DriverVehicleAssignment(driver_id=drv_profile_id, vehicle_id=vehicle.id, assigned_at=datetime.now(timezone.utc), assignment_reason='Smoke test - failed validation', status='Failed_Validation')
        db.session.add(assign)
        db.session.commit()
        sys.exit(1)

    # proceed: update vehicle and create assignment + deployment
    vehicle.assigned_driver_id = driver.id
    vehicle.assigned_driver = driver.username
    vehicle.status = 'Assigned'

    profile = getattr(driver, 'driver_profile', None)
    profile_id = profile.id if profile else None
    assign = DriverVehicleAssignment(driver_id=profile_id, vehicle_id=vehicle.id, assigned_at=datetime.now(timezone.utc), assignment_reason='Smoke test - operational assignment', status='Active')
    db.session.add(assign)
    db.session.commit()

    payload = {
        'vehicle_id': vehicle.id,
        'driver_id': driver.id,
        'project_id': vehicle.project_id,
        'subzone_id': vehicle.subzone_id,
        'deployment_type': 'Standard',
        'route_name': 'Smoke Assign Route',
        'vehicle_fitness_verified': True,
        'driver_license_verified': True,
        'insurance_verified': True,
        'safety_checklist_completed': True,
        'special_instructions': 'Smoke test assign',
        'notes': 'Smoke test assign',
    }

    deployment, error = svc.create_deployment(payload, driver.id)
    if error:
        print('Deployment creation failed:', error)
        sys.exit(1)

    print('Deployment created:', deployment.id, deployment.status, deployment.approval_status)
    sys.exit(0)
