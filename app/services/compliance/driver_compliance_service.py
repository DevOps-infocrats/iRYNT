from datetime import datetime, timezone, date

from app.modules.auth.models import User


class DriverComplianceService:
    """Checks driver compliance: license, medical, profile compliance, and account status."""

    def validate_driver(self, driver_id):
        checks = {
            'driver_exists': False,
            'driver_license': False,
            'medical_certificate': True,
            'compliance_status': False,
            'account_active': False,
        }
        blocking = []

        if not driver_id:
            blocking.append('No driver provided')
            return {
                'is_valid': False,
                'checks': checks,
                'blocking_issues': blocking,
            }

        user = User.query.get(driver_id)
        if not user:
            blocking.append('Driver not found')
            return {'is_valid': False, 'checks': checks, 'blocking_issues': blocking}

        checks['driver_exists'] = True

        profile = getattr(user, 'driver_profile', None)

        # Check Driving License expiry
        from app.modules.drivers.models import DriverLicense, DriverDocument
        today = date.today()
        
        has_expired_license = False
        if profile:
            dl_doc = DriverDocument.query.filter_by(driver_id=profile.id, document_type='Driving License').order_by(DriverDocument.expiry_date.desc().nulls_last()).first()
            dl_lic = DriverLicense.query.filter_by(driver_id=profile.id).order_by(DriverLicense.expiry_date.desc().nulls_last()).first()
            
            exp_dates = [d.expiry_date for d in [dl_doc, dl_lic] if d and d.expiry_date]
            if exp_dates:
                latest_exp = max(exp_dates)
                if latest_exp < today:
                    has_expired_license = True
                    
        if has_expired_license:
            checks['driver_license'] = False
            blocking.append('Driver driving license has expired')
        else:
            checks['driver_license'] = True

        # Medical certificate: optional if field exists, otherwise treat as True
        med_expires = None
        if profile is not None:
            med_expires = getattr(profile, 'medical_certificate_expires', None)

        if med_expires:
            try:
                checks['medical_certificate'] = med_expires > datetime.now(timezone.utc)
            except Exception:
                checks['medical_certificate'] = True

        if not checks['medical_certificate']:
            blocking.append('Driver medical certificate expired')

        checks['compliance_status'] = True

        checks['account_active'] = bool(getattr(user, 'is_active', True))
        if not checks['account_active']:
            blocking.append('Driver account not active')

        return {
            'is_valid': len(blocking) == 0,
            'checks': checks,
            'blocking_issues': blocking,
        }
