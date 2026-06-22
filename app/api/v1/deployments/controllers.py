from app.modules.deployments.services import DeploymentService
from app.domain.auth.policies.auth_policy import has_role

class DeploymentsApiController:
    def __init__(self):
        self.deployment_service = DeploymentService()

    def get_current_deployment(self, actor):
        """
        Retrieves the current active deployment details for the authenticated user.
        Supports both Driver and Helper roles.
        """
        deployment = None
        helper_assignment = None

        if has_role(actor, 'Driver'):
            deployment = self.deployment_service.repository.get_driver_current_deployment(actor.id)
        elif has_role(actor, 'Helper'):
            from app.modules.deployments.models import HelperAssignment
            helper_assignment = HelperAssignment.query.filter_by(
                helper_id=actor.id,
                status='Active'
            ).first()
            if helper_assignment:
                if helper_assignment.assigned_vehicle_id:
                    deployment = self.deployment_service.repository.get_vehicle_current_deployment(
                        helper_assignment.assigned_vehicle_id
                    )
                if not deployment and helper_assignment.assigned_driver_id:
                    deployment = self.deployment_service.repository.get_driver_current_deployment(
                        helper_assignment.assigned_driver_id
                    )
                if not deployment:
                    # Fallback to any active deployment in helper's assigned project + subzone
                    from app.modules.deployments.models import VehicleDeployment
                    deployment = VehicleDeployment.query.filter_by(
                        project_id=helper_assignment.project_id,
                        subzone_id=helper_assignment.subzone_id,
                        status='Active'
                    ).first()

        # Final fallback check regardless of role cache
        if not deployment and not helper_assignment:
            deployment = self.deployment_service.repository.get_driver_current_deployment(actor.id)

        # Build response payload
        if deployment:
            data = {
                'project': deployment.project.project_name if deployment.project else "",
                'circle': deployment.project.circle.circle_name if (deployment.project and deployment.project.circle) else "",
                'subzone': deployment.subzone.subzone_name if deployment.subzone else "",
                'vehicle_number': deployment.vehicle.vehicle_number if deployment.vehicle else "",
                'status': deployment.status or ""
            }
        elif helper_assignment:
            data = {
                'project': helper_assignment.project.project_name if helper_assignment.project else "",
                'circle': helper_assignment.circle.circle_name if helper_assignment.circle else "",
                'subzone': helper_assignment.subzone.subzone_name if helper_assignment.subzone else "",
                'vehicle_number': helper_assignment.assigned_vehicle.vehicle_number if helper_assignment.assigned_vehicle else "",
                'status': helper_assignment.status or ""
            }
        else:
            data = {
                'project': "",
                'circle': "",
                'subzone': "",
                'vehicle_number': "",
                'status': ""
            }

        return {'success': True, 'data': data, 'status': 200}
