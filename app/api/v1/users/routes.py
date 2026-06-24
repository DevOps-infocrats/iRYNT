from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.modules.auth.models import User
from app.api.v1.attendance.responses import api_success, api_error

api_users_bp = Blueprint('api_users', __name__)

@api_users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return api_error('User not found.', status_code=404)

    return api_success('Profile retrieved successfully.', data=user.to_dict())
