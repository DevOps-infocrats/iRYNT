from app.services.compliance.driver_compliance_service import DriverComplianceService
from app.services.compliance.vehicle_compliance_service import VehicleComplianceService
from app.modules.deployments.models import VehicleDeployment
from app.modules.vehicles.models import Vehicle
from app.modules.auth.models import User
from datetime import datetime, timezone


class AssignmentValidationService:
    """Validates driver + vehicle + assignment-specific constraints."""

    def __init__(self):
        self.driver_checker = DriverComplianceService()
        self.vehicle_checker = VehicleComplianceService()

    def validate_assignment(self, driver_id=None, vehicle_id=None, project_id=None, subzone_id=None):
        checks = {}
        blocking = []

        # Driver checks
        driver_result = self.driver_checker.validate_driver(driver_id)
        checks['driver'] = driver_result['checks']
        if not driver_result['is_valid']:
            blocking.extend(driver_result['blocking_issues'])

        # Vehicle checks
        vehicle_result = self.vehicle_checker.validate_vehicle(vehicle_id)
        checks['vehicle'] = vehicle_result['checks']
        if not vehicle_result['is_valid']:
            blocking.extend(vehicle_result['blocking_issues'])

        # Conflict checks
        conflict_issues = []
        if vehicle_id:
            vehicle = Vehicle.query.get(vehicle_id)
            if vehicle:
                # vehicle currently assigned to another driver
                if vehicle.assigned_driver_id and str(vehicle.assigned_driver_id) != str(driver_id):
                    conflict_issues.append('Vehicle already assigned to another driver')
                # vehicle already has an active deployment
                active_dep = VehicleDeployment.query.filter_by(vehicle_id=vehicle_id).filter(VehicleDeployment.status.in_(['Active', 'Approved'])).first()
                if active_dep:
                    conflict_issues.append('Vehicle has an active deployment')

        if driver_id:
            # driver already has an active deployment
            active_dep_driver = VehicleDeployment.query.filter_by(driver_id=driver_id).filter(VehicleDeployment.status.in_(['Active', 'Approved'])).first()
            if active_dep_driver:
                conflict_issues.append('Driver has an active deployment')

        if conflict_issues:
            blocking.extend(conflict_issues)

        return {
            'is_valid': len(blocking) == 0,
            'checks': checks,
            'blocking_issues': blocking,
        }
