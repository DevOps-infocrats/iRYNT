"""
Permission and Access Control Decorators
Reusable decorators for role-based and permission-based access control
"""

from functools import wraps
from flask import redirect, url_for, abort, jsonify, current_user
from flask_login import current_user as flask_current_user


def permission_required(permission_name):
    """
    Decorator to check if current user has a specific permission.
    
    Usage:
        @permission_required("roles.view")
        def view_roles():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not flask_current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            from app.domain.auth.access import AccessManager
            access_manager = AccessManager(flask_current_user)
            
            if not access_manager.has_permission(permission_name):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_required(roles):
    """
    Decorator to check if current user has any of the specified roles.
    
    Usage:
        @role_required(['Super Admin', 'Admin'])
        def admin_dashboard():
            pass
    """
    if isinstance(roles, str):
        roles = [roles]
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not flask_current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            from app.domain.auth.access import AccessManager
            access_manager = AccessManager(flask_current_user)
            
            if not access_manager.has_role(roles):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def scope_required(scope_type):
    """
    Decorator to check if current user has access to a specific scope.
    
    Usage:
        @scope_required("circle")
        def view_circle_data():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not flask_current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            from app.domain.auth.access import AccessManager
            access_manager = AccessManager(flask_current_user)
            
            # Assuming scope is passed as query parameter or route argument
            scope_id = kwargs.get(f'{scope_type}_id')
            
            if not scope_id:
                abort(400)
            
            if not access_manager.has_scope(**{f'{scope_type}_id': scope_id}):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def module_access_required(module_name, action='view'):
    """
    Decorator to check if current user has access to a specific module action.
    
    Usage:
        @module_access_required("users", "create")
        def create_user():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not flask_current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            from app.modules.roles.repository import RolesRepository
            from app.domain.auth.access import AccessManager
            
            access_manager = AccessManager(flask_current_user)
            repo = RolesRepository()
            
            # Get user's primary role
            if not flask_current_user.primary_role:
                abort(403)
            
            # Check module access
            module_access = repo.get_role_module_access(flask_current_user.primary_role.id)
            module_access_dict = {m.module_name: m for m in module_access}
            
            if module_name not in module_access_dict:
                abort(403)
            
            access = module_access_dict[module_name]
            can_action = getattr(access, f'can_{action}', False)
            
            if not can_action:
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def workflow_permission_required(workflow_type, required_level=1):
    """
    Decorator to check if current user has workflow permissions.
    
    Usage:
        @workflow_permission_required("deployment", required_level=2)
        def approve_deployment():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not flask_current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            from app.modules.roles.repository import RolesRepository
            
            if not flask_current_user.primary_role:
                abort(403)
            
            repo = RolesRepository()
            workflows = repo.get_role_workflow_permissions(flask_current_user.primary_role.id)
            workflow = next((w for w in workflows if w.workflow_type == workflow_type), None)
            
            if not workflow or workflow.approval_level < required_level:
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def audit_required(action):
    """
    Decorator to automatically log access attempts.
    
    Usage:
        @audit_required("view_role")
        def view_role(role_id):
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from app.modules.roles.repository import RolesRepository
            from flask import request
            
            repo = RolesRepository()
            
            # Log the action
            try:
                repo.create_audit_log(
                    action=action,
                    entity_type='access',
                    user_id=flask_current_user.id if flask_current_user.is_authenticated else None,
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string if request.user_agent else None,
                )
            except Exception as e:
                # Don't fail the request if audit logging fails
                current_app.logger.error(f"Audit logging failed: {str(e)}")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def super_admin_only(f):
    """
    Decorator to restrict access to super admin users only.
    
    Usage:
        @super_admin_only
        def admin_action():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not flask_current_user.is_authenticated or not flask_current_user.is_superadmin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def api_permission_required(permission_name):
    """
    Decorator for API endpoints to check permissions (returns JSON error).
    
    Usage:
        @api_permission_required("roles.edit")
        def api_update_role():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not flask_current_user.is_authenticated:
                return jsonify({'error': 'Unauthorized'}), 401
            
            from app.domain.auth.access import AccessManager
            access_manager = AccessManager(flask_current_user)
            
            if not access_manager.has_permission(permission_name):
                return jsonify({'error': 'Forbidden'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
