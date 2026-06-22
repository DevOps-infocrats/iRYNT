from app.modules.vehicles.services import VehicleService
from app.modules.deployments.services import DeploymentService
from app.modules.vehicles.models import Vehicle
from app.domain.auth.policies.auth_policy import has_role

class VehiclesApiController:
    def __init__(self):
        self.vehicle_service = VehicleService()
        self.deployment_service = DeploymentService()

    def get_current_vehicle(self, actor):
        """
        Retrieves the current vehicle details for the authenticated user.
        Supports both Driver and Helper roles.
        """
        vehicle = None
        helper_assignment = None

        if has_role(actor, 'Driver'):
            deployment = self.deployment_service.repository.get_driver_current_deployment(actor.id)
            if deployment:
                vehicle = deployment.vehicle
            if not vehicle:
                vehicle = Vehicle.query.filter_by(assigned_driver_id=actor.id).first()
        elif has_role(actor, 'Helper'):
            from app.modules.deployments.models import HelperAssignment
            helper_assignment = HelperAssignment.query.filter_by(
                helper_id=actor.id,
                status='Active'
            ).first()
            if helper_assignment:
                if helper_assignment.assigned_vehicle_id:
                    vehicle = self.vehicle_service.get_vehicle(helper_assignment.assigned_vehicle_id)
                if not vehicle and helper_assignment.assigned_driver_id:
                    driver_dep = self.deployment_service.repository.get_driver_current_deployment(
                        helper_assignment.assigned_driver_id
                    )
                    if driver_dep:
                        vehicle = driver_dep.vehicle
                    else:
                        vehicle = Vehicle.query.filter_by(assigned_driver_id=helper_assignment.assigned_driver_id).first()
                if not vehicle:
                    from app.modules.deployments.models import VehicleDeployment
                    dep = VehicleDeployment.query.filter_by(
                        project_id=helper_assignment.project_id,
                        subzone_id=helper_assignment.subzone_id,
                        status='Active'
                    ).first()
                    if dep:
                        vehicle = dep.vehicle

        # Final fallback check regardless of role cache
        if not vehicle and not helper_assignment:
            deployment = self.deployment_service.repository.get_driver_current_deployment(actor.id)
            if deployment:
                vehicle = deployment.vehicle
            if not vehicle:
                vehicle = Vehicle.query.filter_by(assigned_driver_id=actor.id).first()

        # Build response payload
        if vehicle:
            data = {
                'vehicle_number': vehicle.vehicle_number or "",
                'vehicle_type': vehicle.vehicle_type or "",
                'odometer': vehicle.vehicle_running if vehicle.vehicle_running is not None else "",
                'insurance_expiry': vehicle.insurance_expiry.isoformat() if vehicle.insurance_expiry else "",
                'fitness_expiry': vehicle.fitness_expiry.isoformat() if vehicle.fitness_expiry else ""
            }
        else:
            data = {
                'vehicle_number': "",
                'vehicle_type': "",
                'odometer': "",
                'insurance_expiry': "",
                'fitness_expiry': ""
            }

        return {'success': True, 'data': data, 'status': 200}
