from datetime import datetime, timezone

from app.modules.vehicles.models import Vehicle


class VehicleComplianceService:
    """Checks vehicle compliance: insurance, fitness, permits, PUC, and status."""

    def validate_vehicle(self, vehicle_id):
        checks = {
            'vehicle_exists': False,
            'vehicle_insurance': False,
            'vehicle_fitness': False,
            'vehicle_permit': True,
            'vehicle_puc': False,
            'deployment_allowed': False,
            'vehicle_active': False,
        }
        blocking = []

        if not vehicle_id:
            blocking.append('No vehicle provided')
            return {'is_valid': False, 'checks': checks, 'blocking_issues': blocking}

        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            blocking.append('Vehicle not found')
            return {'is_valid': False, 'checks': checks, 'blocking_issues': blocking}

        checks['vehicle_exists'] = True
        checks['vehicle_insurance'] = getattr(vehicle, 'insurance_status', None) == 'Valid'
        if not checks['vehicle_insurance']:
            blocking.append('Vehicle insurance not valid')

        checks['vehicle_fitness'] = getattr(vehicle, 'fitness_status', None) == 'Valid'
        if not checks['vehicle_fitness']:
            blocking.append('Vehicle fitness not valid')

        checks['vehicle_puc'] = getattr(vehicle, 'puc_status', None) == 'Valid'
        if not checks['vehicle_puc']:
            blocking.append('Vehicle PUC not valid')

        # Permit status is optional; treat missing field as True
        checks['vehicle_permit'] = getattr(vehicle, 'permit_status', None) in (None, 'Valid')
        if not checks['vehicle_permit']:
            blocking.append('Vehicle permit not valid')

        checks['deployment_allowed'] = bool(getattr(vehicle, 'deployment_allowed', False))
        if not checks['deployment_allowed']:
            blocking.append('Vehicle not allowed for deployment')

        checks['vehicle_active'] = getattr(vehicle, 'status', None) in ('Available', 'Active', 'Assigned')
        if not checks['vehicle_active']:
            blocking.append('Vehicle is not active/available')

        # Check odometer maximum operational limit
        odometer = getattr(vehicle, 'vehicle_running', 0.0) or 0.0
        resolved_status = getattr(vehicle, 'resolved_status', None)
        if odometer >= 150000 or resolved_status == 'Deployment Restricted':
            blocking.append('Vehicle has crossed maximum operational KM limit and cannot be deployed.')

        return {
            'is_valid': len(blocking) == 0,
            'checks': checks,
            'blocking_issues': blocking,
        }
