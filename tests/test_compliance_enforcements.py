import pytest
from app import create_app, db
from app.modules.auth.models import User, Role
from app.modules.drivers.models import DriverProfile, DriverAttendance
from app.modules.vehicles.models import Vehicle
from app.modules.deployments.models import VehicleDeployment
from app.modules.notifications.models import Notification
from app.modules.notifications.helpers import create_notification_safe
from datetime import datetime, date, timedelta, timezone
from unittest.mock import patch

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

def test_vehicle_status_precedence(app):
    with app.app_context():
        from app.modules.companies.models import Company
        from app.modules.circles.models import Circle
        from app.modules.clients.models import Client
        from app.modules.projects.models import Project
        from app.modules.subzones.models import Subzone
        
        comp = Company(company_name='Test Comp', company_code='TC01', country_id='1', state_id='1', city_id='1', pincode='123456')
        db.session.add(comp)
        db.session.commit()
        
        circ = Circle(company_id=comp.id, circle_code='EC01', circle_name='East Circle')
        db.session.add(circ)
        db.session.commit()
        
        client = Client(company_id=comp.id, circle_id=circ.id, client_code='TCC01', client_name='Test Client')
        db.session.add(client)
        db.session.commit()
        
        proj = Project(company_id=comp.id, circle_id=circ.id, client_id=client.id, project_code='TP01', project_name='Test Proj', project_type='Standard', start_date=date.today())
        db.session.add(proj)
        db.session.commit()
        
        subz = Subzone(company_id=comp.id, circle_id=circ.id, client_id=client.id, project_id=proj.id, subzone_code='SZ01', subzone_name='Subzone 1', subzone_type='Standard')
        db.session.add(subz)
        db.session.commit()
        
        # 1. Normal vehicle (odometer=0) -> status is Available
        v1 = Vehicle(
            company_id=comp.id, circle_id=circ.id, client_id=client.id,
            project_id=proj.id, subzone_id=subz.id, vehicle_number='KA01AB1234',
            vehicle_type='Truck', vehicle_category='Heavy', vehicle_brand='Tata',
            vehicle_model='LPT', status='Available', vehicle_running=0.0
        )
        db.session.add(v1)
        db.session.commit()
        assert v1.resolved_status == 'Available'
        
        # 2. Maintenance Warning (odometer=140000)
        v1.vehicle_running = 142000.0
        db.session.commit()
        assert v1.resolved_status == 'Maintenance Warning'
        
        # 3. Maintenance Required (expired document)
        v1.vehicle_running = 10000.0
        v1.insurance_expiry = date.today() - timedelta(days=1)
        db.session.commit()
        assert v1.resolved_status == 'Maintenance Required'
        
        # 4. Deployment Restricted (odometer=150000)
        v1.vehicle_running = 155000.0
        db.session.commit()
        assert v1.resolved_status == 'Deployment Restricted'

def test_odometer_anomaly_detection(app):
    from app.modules.attendance.services import AttendanceService
    
    with app.app_context():
        role_driver = Role.query.filter_by(name='Driver').first()
        if not role_driver:
            role_driver = Role(name='Driver')
            db.session.add(role_driver)
            db.session.commit()
        
        driver_user = User(username='driver_odo_anomaly', email='driver_odo_anomaly@test.com', role_id=role_driver.id)
        driver_user.set_password('pass123')
        db.session.add(driver_user)
        db.session.commit()
        driver_user.roles.append(role_driver)
        db.session.commit()
        
        profile = DriverProfile(user_id=driver_user.id, active=True)
        db.session.add(profile)
        db.session.commit()
        
        from app.modules.companies.models import Company
        from app.modules.circles.models import Circle
        from app.modules.clients.models import Client
        from app.modules.projects.models import Project
        from app.modules.subzones.models import Subzone
        
        comp = Company(company_name='Test Comp', company_code='TC01', country_id='1', state_id='1', city_id='1', pincode='123456')
        db.session.add(comp)
        db.session.commit()
        
        circ = Circle(company_id=comp.id, circle_code='EC01', circle_name='East Circle')
        db.session.add(circ)
        db.session.commit()
        
        client = Client(company_id=comp.id, circle_id=circ.id, client_code='TCC01', client_name='Test Client')
        db.session.add(client)
        db.session.commit()
        
        proj = Project(company_id=comp.id, circle_id=circ.id, client_id=client.id, project_code='TP01', project_name='Test Proj', project_type='Standard', start_date=date.today())
        db.session.add(proj)
        db.session.commit()
        
        subz = Subzone(company_id=comp.id, circle_id=circ.id, client_id=client.id, project_id=proj.id, subzone_code='SZ01', subzone_name='Subzone 1', subzone_type='Standard')
        db.session.add(subz)
        db.session.commit()
        
        vehicle = Vehicle(
            company_id=comp.id, circle_id=circ.id, client_id=client.id,
            project_id=proj.id, subzone_id=subz.id, vehicle_number='KA01AB1234',
            vehicle_type='Truck', vehicle_category='Heavy', vehicle_brand='Tata',
            vehicle_model='LPT', status='Available', vehicle_running=1000.0
        )
        db.session.add(vehicle)
        db.session.commit()
        
        # Active deployment
        deployment = VehicleDeployment(
            vehicle_id=vehicle.id,
            driver_id=driver_user.id,
            project_id=proj.id,
            subzone_id=subz.id,
            status='Active',
            approval_status='Approved',
            actual_start=datetime.now(timezone.utc)
        )
        db.session.add(deployment)
        db.session.commit()
        
        service = AttendanceService()
        
        with patch.object(service.geo_service, 'validate_attendance_location') as mock_val:
            mock_val.return_value = ({'accuracy': 10.0, 'geo_verified': True, 'geo_status': 'GEO_VERIFIED'}, None)
            
            # Case 1: normal odometer (matches or increases)
            attendance, error = service.mark_attendance(
                driver_profile_id=profile.id,
                action='check_in',
                location_payload={'latitude': '12.9716', 'longitude': '77.5946'},
                actor_id=driver_user.id,
                odometer=1050.0
            )
            assert error is None
            assert attendance.start_odometer == 1050.0
            assert vehicle.vehicle_running == 1050.0
            assert attendance.verification_status is None
            
            # Case 2: anomaly (decreased odometer)
            attendance_out, error_out = service.mark_attendance(
                driver_profile_id=profile.id,
                action='check_out',
                location_payload={'latitude': '12.9716', 'longitude': '77.5946'},
                actor_id=driver_user.id,
                odometer=900.0
            )
            assert error_out is None
            assert attendance_out.end_odometer == 900.0
            # Verification status should flag Requires Verification
            assert attendance_out.verification_status == 'Requires Verification'
            # Vehicle odometer should NOT be updated to the lower value
            assert vehicle.vehicle_running == 1050.0

def test_notification_deduplication(app):
    with app.app_context():
        role_driver = Role.query.filter_by(name='Driver').first()
        if not role_driver:
            role_driver = Role(name='Driver')
            db.session.add(role_driver)
            db.session.commit()
        
        user = User(username='driver_notif_test', email='notif@test.com', role_id=role_driver.id)
        user.set_password('pass123')
        db.session.add(user)
        db.session.commit()
        
        # Call create_notification_safe twice with identical message in compliance
        create_notification_safe(
            user_id=user.id,
            message="140000 KM Warning: Vehicle KA01AB1234 has reached threshold.",
            module="vehicles",
            priority="Warning"
        )
        
        # Check DB
        notifs_1 = Notification.query.filter_by(user_id=user.id).all()
        assert len(notifs_1) == 1
        assert notifs_1[0].priority == 'Warning'
        
        # Second call should be deduplicated (ignored)
        create_notification_safe(
            user_id=user.id,
            message="140000 KM Warning: Vehicle KA01AB1234 has reached threshold.",
            module="vehicles",
            priority="Warning"
        )
        
        notifs_2 = Notification.query.filter_by(user_id=user.id).all()
        assert len(notifs_2) == 1  # Still 1!


def test_lifecycle_compliance_alerts(app):
    with app.app_context():
        from app.modules.companies.models import Company
        from app.modules.circles.models import Circle
        from app.modules.clients.models import Client
        from app.modules.projects.models import Project
        from app.modules.subzones.models import Subzone
        from app.services.compliance.alerts_service import run_compliance_alerts
        from app.services.compliance.driver_compliance_service import DriverComplianceService
        from app.modules.drivers.models import DriverDocument, DriverLicense
        
        # Setup basic company structure
        comp = Company(company_name='Lifecycle Comp', company_code='LC01', country_id='1', state_id='1', city_id='1', pincode='123456')
        db.session.add(comp)
        db.session.commit()
        
        circ = Circle(company_id=comp.id, circle_code='LC_EC01', circle_name='East Circle')
        db.session.add(circ)
        db.session.commit()
        
        client = Client(company_id=comp.id, circle_id=circ.id, client_code='LC_TCC01', client_name='Test Client')
        db.session.add(client)
        db.session.commit()
        
        proj = Project(company_id=comp.id, circle_id=circ.id, client_id=client.id, project_code='LC_TP01', project_name='Test Proj', project_type='Standard', start_date=date.today())
        db.session.add(proj)
        db.session.commit()
        
        subz = Subzone(company_id=comp.id, circle_id=circ.id, client_id=client.id, project_id=proj.id, subzone_code='LC_SZ01', subzone_name='Subzone 1', subzone_type='Standard')
        db.session.add(subz)
        db.session.commit()
        
        # Seed Compliance Officer role and user so alerts will get generated for them
        role_officer = Role.query.filter_by(name='Compliance Officer').first()
        if not role_officer:
            role_officer = Role(name='Compliance Officer')
            db.session.add(role_officer)
            db.session.commit()
            
        officer_user = User(username='compliance_off', email='officer@test.com', role_id=role_officer.id)
        officer_user.set_password('pass123')
        db.session.add(officer_user)
        db.session.commit()
        officer_user.roles.append(role_officer)
        db.session.commit()
        
        # 1. Test Odometer Alert Warning (140000 KM)
        v_warn = Vehicle(
            company_id=comp.id, circle_id=circ.id, client_id=client.id,
            project_id=proj.id, subzone_id=subz.id, vehicle_number='KA01WARN',
            vehicle_type='Truck', vehicle_category='Heavy', vehicle_brand='Tata',
            vehicle_model='LPT', status='Available', vehicle_running=142000.0
        )
        db.session.add(v_warn)
        
        # 2. Test Odometer Alert Critical (150000 KM)
        v_crit = Vehicle(
            company_id=comp.id, circle_id=circ.id, client_id=client.id,
            project_id=proj.id, subzone_id=subz.id, vehicle_number='KA01CRIT',
            vehicle_type='Truck', vehicle_category='Heavy', vehicle_brand='Tata',
            vehicle_model='LPT', status='Available', vehicle_running=155000.0,
            deployment_allowed=True
        )
        db.session.add(v_crit)
        
        # 3. Test Vehicle Age Alert Warning (5y 6m)
        today = date(2026, 11, 15)
        v_age_warn = Vehicle(
            company_id=comp.id, circle_id=circ.id, client_id=client.id,
            project_id=proj.id, subzone_id=subz.id, vehicle_number='KA01AGEW',
            vehicle_type='Truck', vehicle_category='Heavy', vehicle_brand='Tata',
            vehicle_model='LPT', status='Available', vehicle_running=0.0
        )
        # 2026 - 2021 = 5 years. total_months = 5 * 12 + 11 - 1 = 70 months (Warning range: 66 to 71)
        v_age_warn.manufacturing_year = '2021'
        db.session.add(v_age_warn)
        
        v_age_crit = Vehicle(
            company_id=comp.id, circle_id=circ.id, client_id=client.id,
            project_id=proj.id, subzone_id=subz.id, vehicle_number='KA01AGEC',
            vehicle_type='Truck', vehicle_category='Heavy', vehicle_brand='Tata',
            vehicle_model='LPT', status='Available', vehicle_running=0.0
        )
        # 2026 - 2020 = 6 years. total_months = 6 * 12 + 11 - 1 = 82 months (Critical range: >= 72)
        v_age_crit.manufacturing_year = '2020'
        db.session.add(v_age_crit)
        
        # 4. Test Driver License Expiring & Expired
        role_driver = Role.query.filter_by(name='Driver').first()
        if not role_driver:
            role_driver = Role(name='Driver')
            db.session.add(role_driver)
            db.session.commit()
            
        d_warn_user = User(username='d_warn', email='dwarn@test.com', role_id=role_driver.id)
        d_warn_user.set_password('pass123')
        db.session.add(d_warn_user)
        db.session.commit()
        d_warn_profile = DriverProfile(user_id=d_warn_user.id, active=True, compliance_status='Verified')
        db.session.add(d_warn_profile)
        db.session.commit()
        
        d_warn_doc = DriverDocument(
            driver_id=d_warn_profile.id,
            document_type='Driving License',
            file_name='dl.pdf',
            storage_path='dl.pdf',
            expiry_date=today + timedelta(days=15) # Expiring soon
        )
        db.session.add(d_warn_doc)
        
        d_crit_user = User(username='d_crit', email='dcrit@test.com', role_id=role_driver.id)
        d_crit_user.set_password('pass123')
        db.session.add(d_crit_user)
        db.session.commit()
        d_crit_profile = DriverProfile(user_id=d_crit_user.id, active=True, compliance_status='Verified')
        db.session.add(d_crit_profile)
        db.session.commit()
        
        d_crit_doc = DriverDocument(
            driver_id=d_crit_profile.id,
            document_type='Driving License',
            file_name='dl_crit.pdf',
            storage_path='dl_crit.pdf',
            expiry_date=today - timedelta(days=1) # Expired
        )
        db.session.add(d_crit_doc)
        db.session.commit()
        
        # Run compliance alerts and verify under mocked date context
        with patch('app.services.compliance.alerts_service.date') as mock_date_alerts, \
             patch('app.services.compliance.driver_compliance_service.date') as mock_date_drv:
            
            mock_date_alerts.today.return_value = today
            mock_date_drv.today.return_value = today
            
            run_compliance_alerts()
            
            # Verify Critical vehicle status changed
            assert v_crit.deployment_allowed is False
            
            # Verify critical odometer notification created
            crit_notif = Notification.query.filter(
                Notification.related_type == 'vehicle',
                Notification.related_id == v_crit.id,
                Notification.message.like('%Vehicle Deployment Limit Reached%')
            ).first()
            assert crit_notif is not None
            assert crit_notif.priority == 'Critical'
            
            # Verify warning odometer notification created
            warn_notif = Notification.query.filter(
                Notification.related_type == 'vehicle',
                Notification.related_id == v_warn.id,
                Notification.message.like('%Vehicle Approaching Service Limit%')
            ).first()
            assert warn_notif is not None
            assert warn_notif.priority == 'Warning'
            
            # Verify age warning notification created
            age_warn_notif = Notification.query.filter(
                Notification.related_type == 'vehicle',
                Notification.related_id == v_age_warn.id,
                Notification.message.like('%Vehicle Approaching Age Limit%')
            ).first()
            assert age_warn_notif is not None
            assert age_warn_notif.priority == 'Warning'
            
            # Verify age critical notification created
            age_crit_notif = Notification.query.filter(
                Notification.related_type == 'vehicle',
                Notification.related_id == v_age_crit.id,
                Notification.message.like('%Vehicle Age Compliance Expired%')
            ).first()
            assert age_crit_notif is not None
            assert age_crit_notif.priority == 'Critical'
            
            # Verify driver compliance status set to Incomplete
            assert d_crit_profile.compliance_status == 'Incomplete'
            
            # Verify driver deployment eligibility is blocked
            drv_service = DriverComplianceService()
            val_res = drv_service.validate_driver(d_crit_user.id)
            assert val_res['is_valid'] is False
            assert 'Driver driving license has expired' in val_res['blocking_issues']
            
            # Verify duplicate prevention: run alerts again and ensure no duplicates
            count_before = Notification.query.count()
            run_compliance_alerts()
            count_after = Notification.query.count()
            assert count_before == count_after

