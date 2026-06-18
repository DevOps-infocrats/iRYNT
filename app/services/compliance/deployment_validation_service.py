from app.services.compliance.driver_compliance_service import DriverComplianceService
from app.services.compliance.vehicle_compliance_service import VehicleComplianceService


class DeploymentValidationService:
    """Centralized validator orchestrating driver and vehicle checks."""

    def __init__(self):
        self.driver_service = DriverComplianceService()
        self.vehicle_service = VehicleComplianceService()

    def validate_deployment(self, driver_id=None, vehicle_id=None, project_id=None, subzone_id=None):
        # Run driver checks
        driver_result = self.driver_service.validate_driver(driver_id) if driver_id else {
            'is_valid': True, 'checks': {}, 'blocking_issues': []
        }

        # Run vehicle checks
        vehicle_result = self.vehicle_service.validate_vehicle(vehicle_id) if vehicle_id else {
            'is_valid': True, 'checks': {}, 'blocking_issues': []
        }

        checks = {
            'driver': driver_result['checks'],
            'vehicle': vehicle_result['checks'],
        }

        blocking = []
        blocking.extend(driver_result.get('blocking_issues', []))
        blocking.extend(vehicle_result.get('blocking_issues', []))

        is_valid = len(blocking) == 0

        return {
            'is_valid': is_valid,
            'checks': checks,
            'blocking_issues': blocking,
        }
