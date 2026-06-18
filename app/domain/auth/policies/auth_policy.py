from flask_jwt_extended import get_jwt, verify_jwt_in_request
from flask_login import current_user

from app.domain.auth.access import AccessManager


def _claims():
    try:
        verify_jwt_in_request(optional=True)
        return get_jwt()
    except TypeError:
        try:
            verify_jwt_in_request()
            return get_jwt()
        except Exception:
            return {}
    except Exception:
        return {}


def has_role(user=None, roles=None):
    if roles is None:
        roles = user
        user = current_user
    if roles is None:
        return True
    manager = AccessManager(user, _claims())
    return manager.has_role(roles)


def has_permission(user=None, permission_name=None):
    if permission_name is None:
        permission_name = user
        user = current_user
    manager = AccessManager(user, _claims())
    return manager.has_permission(permission_name)


def has_scope(user=None, company_id=None, circle_id=None):
    if company_id is None and circle_id is None and user is not None and not hasattr(user, 'is_authenticated'):
        company_id = user
        user = current_user
    manager = AccessManager(user, _claims())
    return manager.has_scope(company_id=company_id, circle_id=circle_id)

