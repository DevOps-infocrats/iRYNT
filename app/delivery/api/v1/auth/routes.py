from flask import Blueprint, jsonify, request

from app.delivery.api.v1.auth.controllers import AuthApiController

api_auth_bp = Blueprint('api_auth', __name__)
controller = AuthApiController()


def _json_payload():
    return request.get_json(silent=True) or {}


@api_auth_bp.route('/login', methods=['POST'])
def login():
    payload = _json_payload()
    identifier = payload.get('email') or payload.get('username') or payload.get('identifier')
    password = payload.get('password')
    remember_me = bool(payload.get('remember_me', False))
    result = controller.login(
        identifier=identifier,
        password=password,
        remember_me=remember_me,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
    )
    status = 200 if result.get('success') else 401
    data = {
        'access_token': result.get('access_token'),
        'refresh_token': result.get('refresh_token'),
        'user': result.get('user').to_dict() if result.get('user') else None,
        'permissions': result.get('user').permissions if result.get('user') else [],
    }
    return jsonify(success=result.get('success', False), message=result.get('message'), data=data), status


@api_auth_bp.route('/refresh', methods=['POST'])
def refresh():
    payload = _json_payload()
    refresh_token = payload.get('refresh_token')
    result = controller.refresh(refresh_token)
    status = 200 if result.get('success') else 401
    return jsonify(success=result.get('success', False), message=result.get('message'), data={
        'access_token': result.get('access_token'),
        'refresh_token': result.get('refresh_token'),
    }), status


@api_auth_bp.route('/logout', methods=['POST'])
def logout():
    payload = _json_payload()
    refresh_token = payload.get('refresh_token')
    result = controller.logout(refresh_token=refresh_token)
    status = 200 if result.get('success') else 400
    return jsonify(success=result.get('success', False), message=result.get('message')), status


@api_auth_bp.route('/password/forgot', methods=['POST'])
def forgot_password():
    payload = _json_payload()
    email = payload.get('email')
    result = controller.forgot_password(email=email)
    if result.get('success'):
        return jsonify(success=True, message='If this account exists, reset instructions have been sent.'), 200
    return jsonify(success=True, message='If this account exists, reset instructions have been sent.'), 200


@api_auth_bp.route('/password/reset', methods=['POST'])
def reset_password():
    payload = _json_payload()
    token = payload.get('token')
    new_password = payload.get('new_password')
    result = controller.reset_password(token=token, new_password=new_password)
    status = 200 if result.get('success') else 400
    return jsonify(success=result.get('success', False), message=result.get('message')), status
