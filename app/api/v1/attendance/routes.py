from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app.core.decorators import permission_required
from app.modules.auth.models import User
from app.api.v1.attendance.controllers import AttendanceApiController
from app.api.v1.attendance.gps_controller import GpsApiController
from app.api.v1.attendance.serializers import (
    CheckInRequestSchema,
    CheckOutRequestSchema,
    GPSSyncRequestSchema,
    AttendanceResponseSchema
)
from app.api.v1.attendance.validators import validate_role_attendance_requirements
from app.api.v1.attendance.responses import api_success, api_error
from app.modules.drivers.models import DriverProfile

api_attendance_bp = Blueprint('api_attendance', __name__)

attendance_controller = AttendanceApiController()
gps_controller = GpsApiController()

@api_attendance_bp.route('/check-in', methods=['POST'])
@jwt_required()
@permission_required('attendance.mark')
def check_in():
    user_id = get_jwt_identity()
    actor = User.query.get(user_id)
    if not actor:
        return api_error('User not found.', status_code=404)

    payload = request.get_json(silent=True) or {}
    schema = CheckInRequestSchema()
    try:
        data = schema.load(payload)
    except ValidationError as err:
        return api_error('Validation failed.', errors=err.messages, status_code=400)

    # Perform role validation before processing
    driver_profile_id = data.get('driver_profile_id')
    driver_profile = DriverProfile.query.get(driver_profile_id)
    if not driver_profile:
        return api_error('Driver profile could not be found.', status_code=404)

    try:
        validate_role_attendance_requirements(actor, driver_profile, 'check_in', data)
    except ValidationError as err:
        return api_error(err.messages[0], status_code=400)

    result = attendance_controller.mark('check_in', data, actor)
    if not result.get('success'):
        return api_error(result.get('message'), status_code=result.get('status', 400))

    serialized_data = AttendanceResponseSchema().dump(result.get('attendance'))
    return api_success('Checked in successfully.', data=serialized_data)


@api_attendance_bp.route('/check-out', methods=['POST'])
@jwt_required()
@permission_required('attendance.mark')
def check_out():
    user_id = get_jwt_identity()
    actor = User.query.get(user_id)
    if not actor:
        return api_error('User not found.', status_code=404)

    payload = request.get_json(silent=True) or {}
    schema = CheckOutRequestSchema()
    try:
        data = schema.load(payload)
    except ValidationError as err:
        return api_error('Validation failed.', errors=err.messages, status_code=400)

    # Perform role validation before processing
    driver_profile_id = data.get('driver_profile_id')
    driver_profile = DriverProfile.query.get(driver_profile_id)
    if not driver_profile:
        return api_error('Driver profile could not be found.', status_code=404)

    try:
        validate_role_attendance_requirements(actor, driver_profile, 'check_out', data)
    except ValidationError as err:
        return api_error(err.messages[0], status_code=400)

    result = attendance_controller.mark('check_out', data, actor)
    if not result.get('success'):
        return api_error(result.get('message'), status_code=result.get('status', 400))

    serialized_data = AttendanceResponseSchema().dump(result.get('attendance'))
    return api_success('Checked out successfully.', data=serialized_data)


@api_attendance_bp.route('/gps/sync', methods=['POST'])
@jwt_required()
@permission_required('attendance.mark')
def gps_sync():
    user_id = get_jwt_identity()
    actor = User.query.get(user_id)
    if not actor:
        return api_error('User not found.', status_code=404)

    payload = request.get_json(silent=True) or {}
    schema = GPSSyncRequestSchema()
    try:
        data = schema.load(payload)
    except ValidationError as err:
        return api_error('Validation failed.', errors=err.messages, status_code=400)

    result = gps_controller.sync_gps(data, actor)
    if not result.get('success'):
        return api_error(result.get('message'), status_code=result.get('status', 400))

    return api_success(result.get('message'))


@api_attendance_bp.route('/history', methods=['GET'])
@jwt_required()
@permission_required('attendance.mark')
def get_attendance_history():
    """
    GET /api/v1/attendance/history
    Returns the attendance history for the authenticated user.
    """
    user_id = get_jwt_identity()
    actor = User.query.get(user_id)
    if not actor:
        return api_error('User not found.', status_code=404)

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    search_query = request.args.get('search_query')

    filters = {
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query
    }

    result = attendance_controller.get_history(actor, filters, page, per_page)
    if not result.get('success'):
        return api_error(result.get('message'), status_code=result.get('status', 400))

    serialized_records = AttendanceResponseSchema(many=True).dump(result.get('records'))

    return api_success(
        'Attendance history retrieved successfully.',
        data={
            'records': serialized_records,
            'total': result.get('total'),
            'page': result.get('page'),
            'per_page': result.get('per_page')
        }
    )

