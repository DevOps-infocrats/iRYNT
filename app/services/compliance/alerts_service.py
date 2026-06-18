from app.services.compliance.document_compliance import build_driver_compliance, build_vehicle_compliance
from app.modules.notifications.helpers import create_notification_safe, create_notifications_for_roles_safe
from app.modules.drivers.models import DriverProfile, DriverLicense, DriverDocument
from app.modules.vehicles.models import Vehicle
from datetime import date


def run_compliance_alerts(driver_limit: int = None, vehicle_limit: int = None, days_threshold: int = 30):
    """Scan driver and vehicle compliance and create role-targeted alerts.

    This is intentionally idempotent at the notification level (creates new notifications each run).
    Intended to be invoked by a scheduled job or manually via an admin route.
    """
    driver_rows = DriverProfile.query.limit(driver_limit).all() if driver_limit else DriverProfile.query.all()
    vehicle_rows = Vehicle.query.limit(vehicle_limit).all() if vehicle_limit else Vehicle.query.all()

    roles_to_notify = ['Compliance Officer', 'Compliance Manager']

    results = {'drivers': 0, 'vehicles': 0}
    for profile in driver_rows:
        try:
            latest_license = DriverLicense.query.filter_by(driver_id=profile.id).order_by(DriverLicense.expiry_date.desc().nulls_last()).first()
            documents = list(profile.documents.all() if getattr(profile, 'documents', None) else [])
            compliance = build_driver_compliance(profile, documents, latest_license)
            for card in compliance.get('cards', []):
                expiry = card.get('expiry_state') or {}
                days = expiry.get('days')
                label = expiry.get('label')
                if days is None:
                    continue
                # Trigger if expired or within threshold
                if label == 'Expired' or (days <= days_threshold):
                    message = f"Driver {profile.user.username if profile.user else profile.id}: {card['type']} {label}"
                    # Notify compliance team (role-targeted)
                    create_notifications_for_roles_safe(
                        roles_to_notify,
                        message=message,
                        module='compliance',
                        priority='High' if label == 'Expired' or card.get('required') else 'Warning',
                        related_type='driver_document',
                        related_id=str(card.get('id') or profile.id),
                        route=f"/documents/drivers/{profile.id}",
                        metadata={'driver_profile_id': profile.id, 'doc_type': card.get('type')}
                    )
                    # Notify driver
                    if getattr(profile, 'user_id', None):
                        create_notification_safe(
                            user_id=profile.user_id,
                            message=message,
                            module='compliance',
                            priority='High' if label == 'Expired' else 'Warning',
                            related_type='driver_document',
                            related_id=str(card.get('id') or profile.id),
                            route=f"/documents/drivers/{profile.id}",
                            metadata={'driver_profile_id': profile.id, 'doc_type': card.get('type')}
                        )
                    results['drivers'] += 1
        except Exception:
            continue

    for vehicle in vehicle_rows:
        try:
            compliance = build_vehicle_compliance(vehicle)
            for card in compliance.get('cards', []):
                expiry = card.get('expiry_state') or {}
                days = expiry.get('days')
                label = expiry.get('label')
                if days is None:
                    continue
                if label == 'Expired' or (days <= days_threshold):
                    message = f"Vehicle {vehicle.vehicle_number if vehicle else vehicle.id}: {card['type']} {label}"
                    create_notifications_for_roles_safe(
                        roles_to_notify,
                        message=message,
                        module='compliance',
                        priority='High' if label == 'Expired' else 'Warning',
                        related_type='vehicle_document',
                        related_id=str(vehicle.id),
                        route=f"/documents/vehicles",
                        metadata={'vehicle_id': vehicle.id, 'doc_type': card.get('type')}
                    )
                    results['vehicles'] += 1
        except Exception:
            continue

    # Run lifecycle alerts scan
    try:
        from app.extensions import db
        today = date.today()
        
        all_vehicles = Vehicle.query.all()
        all_drivers = DriverProfile.query.all()
        
        # 1. VEHICLE ODOMETER ALERTS
        for vehicle in all_vehicles:
            try:
                odo = vehicle.vehicle_running or 0.0
                # Check Critical threshold (150000 KM)
                if odo >= 150000:
                    msg = f"Vehicle Deployment Limit Reached: Vehicle {vehicle.vehicle_number} has reached {odo} KM and is no longer eligible for deployment."
                    from app.modules.notifications.models import Notification
                    existing = Notification.query.filter(
                        Notification.related_type == 'vehicle',
                        Notification.related_id == vehicle.id,
                        Notification.message.like('%Vehicle Deployment Limit Reached%')
                    ).first()
                    if not existing:
                        create_notifications_for_roles_safe(
                            roles_to_notify,
                            message=msg,
                            module='compliance',
                            priority='Critical',
                            related_type='vehicle',
                            related_id=vehicle.id,
                            route=f"/documents/vehicles",
                            type='expiry'
                        )
                    
                    if vehicle.deployment_allowed:
                        vehicle.deployment_allowed = False
                        db.session.add(vehicle)
                        
                # Check Warning threshold (140000 KM)
                elif odo >= 140000:
                    msg = f"Vehicle Approaching Service Limit: Vehicle {vehicle.vehicle_number} has reached {odo} KM and is approaching the deployment limit of 150000 KM."
                    from app.modules.notifications.models import Notification
                    existing = Notification.query.filter(
                        Notification.related_type == 'vehicle',
                        Notification.related_id == vehicle.id,
                        Notification.message.like('%Vehicle Approaching Service Limit%')
                    ).first()
                    if not existing:
                        create_notifications_for_roles_safe(
                            roles_to_notify,
                            message=msg,
                            module='compliance',
                            priority='Warning',
                            related_type='vehicle',
                            related_id=vehicle.id,
                            route=f"/documents/vehicles",
                            type='expiry'
                        )
            except Exception:
                continue
                
        # 2. VEHICLE AGE ALERTS
        for vehicle in all_vehicles:
            try:
                if vehicle.manufacturing_year:
                    mfg_year = int(vehicle.manufacturing_year)
                    total_months = (today.year - mfg_year) * 12 + today.month - 1
                    
                    # Check Critical (6 Years or More: >= 72 months)
                    if total_months >= 72:
                        msg = f"Vehicle Age Compliance Expired: Vehicle {vehicle.vehicle_number} has crossed the 6-year compliance threshold and requires review."
                        from app.modules.notifications.models import Notification
                        existing = Notification.query.filter(
                            Notification.related_type == 'vehicle',
                            Notification.related_id == vehicle.id,
                            Notification.message.like('%Vehicle Age Compliance Expired%')
                        ).first()
                        if not existing:
                            create_notifications_for_roles_safe(
                                roles_to_notify,
                                message=msg,
                                module='compliance',
                                priority='Critical',
                                related_type='vehicle',
                                related_id=vehicle.id,
                                route=f"/documents/vehicles",
                                type='expiry'
                            )
                    # Check Warning (5 Years 6 Months: >= 66 months)
                    elif total_months >= 66:
                        msg = f"Vehicle Approaching Age Limit: Vehicle {vehicle.vehicle_number} is approaching the 6-year compliance threshold."
                        from app.modules.notifications.models import Notification
                        existing = Notification.query.filter(
                            Notification.related_type == 'vehicle',
                            Notification.related_id == vehicle.id,
                            Notification.message.like('%Vehicle Approaching Age Limit%')
                        ).first()
                        if not existing:
                            create_notifications_for_roles_safe(
                                roles_to_notify,
                                message=msg,
                                module='compliance',
                                priority='Warning',
                                related_type='vehicle',
                                related_id=vehicle.id,
                                route=f"/documents/vehicles",
                                type='expiry'
                            )
            except (ValueError, TypeError):
                continue
                
        # 3. DRIVING LICENSE EXPIRY ALERTS
        for profile in all_drivers:
            try:
                driver_name = profile.user.username if profile.user else (profile.driver_code or "Driver")
                
                # Get expiry date
                exp_date = None
                dl_doc = DriverDocument.query.filter_by(driver_id=profile.id, document_type='Driving License').order_by(DriverDocument.expiry_date.desc().nulls_last()).first()
                dl_lic = DriverLicense.query.filter_by(driver_id=profile.id).order_by(DriverLicense.expiry_date.desc().nulls_last()).first()
                
                exp_dates = [d.expiry_date for d in [dl_doc, dl_lic] if d and d.expiry_date]
                if exp_dates:
                    exp_date = max(exp_dates)
                    
                if exp_date:
                    remaining_days = (exp_date - today).days
                    
                    # Check Expired
                    if remaining_days <= 0:
                        msg = f"Driving License Expired: Driver {driver_name} driving license has expired."
                        from app.modules.notifications.models import Notification
                        existing = Notification.query.filter(
                            Notification.related_type == 'driver_document',
                            Notification.related_id == profile.id,
                            Notification.message.like('%Driving License Expired%')
                        ).first()
                        if not existing:
                            create_notifications_for_roles_safe(
                                roles_to_notify,
                                message=msg,
                                module='compliance',
                                priority='Critical',
                                related_type='driver_document',
                                related_id=profile.id,
                                route=f"/documents/drivers/{profile.id}",
                                type='expiry'
                            )
                        
                        # Update driver compliance status to Incomplete
                        if profile.compliance_status != 'Incomplete':
                            profile.compliance_status = 'Incomplete'
                            db.session.add(profile)
                            
                    # Check 7 Days Before Expiry
                    elif remaining_days <= 7:
                        msg = f"Driving License Expiry Critical: Driver {driver_name} driving license will expire in {remaining_days} days."
                        from app.modules.notifications.models import Notification
                        existing = Notification.query.filter(
                            Notification.related_type == 'driver_document',
                            Notification.related_id == profile.id,
                            Notification.message.like('%Driving License Expiry Critical%')
                        ).first()
                        if not existing:
                            create_notifications_for_roles_safe(
                                roles_to_notify,
                                message=msg,
                                module='compliance',
                                priority='Critical',
                                related_type='driver_document',
                                related_id=profile.id,
                                route=f"/documents/drivers/{profile.id}",
                                type='expiry'
                            )
                            
                    # Check 30 Days Before Expiry
                    elif remaining_days <= 30:
                        msg = f"Driving License Expiring Soon: Driver {driver_name} driving license will expire in {remaining_days} days."
                        from app.modules.notifications.models import Notification
                        existing = Notification.query.filter(
                            Notification.related_type == 'driver_document',
                            Notification.related_id == profile.id,
                            Notification.message.like('%Driving License Expiring Soon%')
                        ).first()
                        if not existing:
                            create_notifications_for_roles_safe(
                                roles_to_notify,
                                message=msg,
                                module='compliance',
                                priority='Warning',
                                related_type='driver_document',
                                related_id=profile.id,
                                route=f"/documents/drivers/{profile.id}",
                                type='expiry'
                            )
            except Exception:
                continue
                
        db.session.commit()
    except Exception as e:
        print(f"Error in compliance lifecycle checks: {e}", flush=True)

    return results


_LAST_CHECK_TIME = None

def trigger_lightweight_compliance_checks():
    """Trigger compliance scans in a throttled way (every 30 minutes)."""
    global _LAST_CHECK_TIME
    import datetime
    now = datetime.datetime.utcnow()
    
    if _LAST_CHECK_TIME is not None:
        elapsed = (now - _LAST_CHECK_TIME).total_seconds()
        if elapsed < 1800:  # 30 minutes
            return False
            
    _LAST_CHECK_TIME = now
    try:
        run_compliance_alerts(driver_limit=20, vehicle_limit=20)
        return True
    except Exception:
        return False

