from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.modules.auth.models import User
from app.api.v1.deployments.controllers import DeploymentsApiController
from app.api.v1.deployments.serializers import DeploymentCurrentResponseSchema
from app.api.v1.deployments.responses import api_success, api_error
from app.domain.auth.policies.auth_policy import has_permission

api_deployments_bp = Blueprint('api_deployments', __name__)
deployments_controller = DeploymentsApiController()

@api_deployments_bp.route('/current', methods=['GET'])
@jwt_required()
def get_current_deployment():
    """
    GET /api/v1/deployments/current
    Returns the current active deployment for the authenticated user.
    """
    user_id = get_jwt_identity()
    actor = User.query.get(user_id)
    if not actor:
        return api_error('User not found.', status_code=404)

    # Check permission: deployments.view or attendance.mark (so helpers can also access it)
    if not (has_permission(actor, 'deployments.view') or has_permission(actor, 'attendance.mark')):
        return api_error('Forbidden access', status_code=403)

    result = deployments_controller.get_current_deployment(actor)
    if not result.get('success'):
        return api_error(result.get('message'), status_code=result.get('status', 400))

    serialized_data = DeploymentCurrentResponseSchema().dump(result.get('data'))
    return api_success('Current deployment retrieved successfully.', data=serialized_data)
