from functools import wraps

from flask import abort
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from flask_login import current_user

from app.domain.auth.access import AccessManager
from app.domain.auth.policies.auth_policy import has_permission, has_role, has_scope


def _jwt_claims():
    try:
        verify_jwt_in_request(optional=True)
        return get_jwt()
    except Exception:
        return {}


def permission_required(permission_name):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if current_user.is_authenticated and has_permission(current_user, permission_name):
                return fn(*args, **kwargs)
            claims = _jwt_claims()
            if claims and permission_name in claims.get('permissions', []):
                return fn(*args, **kwargs)
            abort(403)

        return wrapper

    return decorator


def role_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if current_user.is_authenticated and has_role(current_user, allowed_roles):
                return fn(*args, **kwargs)
            claims = _jwt_claims()
            jwt_role = claims.get('role')
            if jwt_role and jwt_role.lower() in {role.lower() for role in allowed_roles}:
                return fn(*args, **kwargs)
            abort(403)

        return wrapper

    return decorator


def workflow_required(right_name, module=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            manager = AccessManager(current_user)
            if current_user.is_authenticated and manager.has_workflow_right(right_name, module):
                return fn(*args, **kwargs)
            claims = _jwt_claims()
            if claims:
                jwt_permissions = claims.get('permissions', [])
                if isinstance(jwt_permissions, str):
                    jwt_permissions = [jwt_permissions]
                if module:
                    required = f'{module}.{right_name}'
                    if required in jwt_permissions:
                        return fn(*args, **kwargs)
                if right_name in jwt_permissions:
                    return fn(*args, **kwargs)
            abort(403)

        return wrapper

    return decorator


def scope_required(company_id=None, circle_id=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if current_user.is_authenticated and has_scope(current_user, company_id, circle_id):
                return fn(*args, **kwargs)
            claims = _jwt_claims()
            if claims and has_scope(None, company_id or claims.get('company_id'), circle_id or claims.get('circle_id')):
                return fn(*args, **kwargs)
            abort(403)

        return wrapper

    return decorator
