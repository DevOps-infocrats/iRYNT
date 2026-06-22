from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.modules.auth.models import User
from app.api.v1.vehicles.controllers import VehiclesApiController
from app.api.v1.vehicles.serializers import VehicleCurrentResponseSchema
from app.api.v1.vehicles.responses import api_success, api_error
from app.domain.auth.policies.auth_policy import has_permission

api_vehicles_bp = Blueprint('api_vehicles', __name__)
vehicles_controller = VehiclesApiController()

@api_vehicles_bp.route('/current', methods=['GET'])
@jwt_required()
def get_current_vehicle():
    """
    GET /api/v1/vehicles/current
    Returns the current vehicle details for the authenticated user.
    """
    user_id = get_jwt_identity()
    actor = User.query.get(user_id)
    if not actor:
        return api_error('User not found.', status_code=404)

    # Check permission: deployments.view or attendance.mark
    if not (has_permission(actor, 'deployments.view') or has_permission(actor, 'attendance.mark')):
        return api_error('Forbidden access', status_code=403)

    result = vehicles_controller.get_current_vehicle(actor)
    if not result.get('success'):
        return api_error(result.get('message'), status_code=result.get('status', 400))

    serialized_data = VehicleCurrentResponseSchema().dump(result.get('data'))
    return api_success('Current vehicle retrieved successfully.', data=serialized_data)
