"""
Permission Decorators

Decorators for permission and scope-based access control
"""

from functools import wraps
from flask import abort, current_user
from flask_login import login_required


def permission_required(permission_code):
    """
    Decorator to require a specific permission
    
    Usage:
        @permission_required('users.create')
        def create_user():
            ...
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Check if user has the permission
            from app.modules.auth.models import Permission, Role
            from app.extensions import db
            
            permission = Permission.query.filter_by(name=permission_code).first()
            if not permission:
                abort(403)
            
            # Check if user's roles have this permission
            has_permission = False
            for role in current_user.roles:
                if permission in role.permissions:
                    has_permission = True
                    break
            
            # Also check primary role
            if not has_permission and current_user.primary_role:
                if permission in current_user.primary_role.permissions:
                    has_permission = True
            
            if not has_permission:
                abort(403)
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def scope_required(scope_type):
    """
    Decorator to require a specific scope access
    
    Usage:
        @scope_required('company')
        def company_view():
            ...
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Check if user has access to this scope
            from app.modules.roles.models import RoleScope
            from app.extensions import db
            
            has_scope = False
            for role in current_user.roles:
                scope = RoleScope.query.filter_by(
                    role_id=role.id,
                    scope_type__code=scope_type
                ).first()
                if scope:
                    has_scope = True
                    break
            
            if not has_scope:
                abort(403)
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def workflow_authority_required(workflow_type, authority_type='approve'):
    """
    Decorator to require workflow authority
    
    Usage:
        @workflow_authority_required('deployment', 'approve')
        def approve_deployment():
            ...
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Check workflow authority
            from app.modules.roles.models import WorkflowPermission
            
            has_authority = False
            for role in current_user.roles:
                workflow_perm = WorkflowPermission.query.filter_by(
                    role_id=role.id,
                    workflow_type=workflow_type
                ).first()
                
                if workflow_perm:
                    if authority_type == 'approve' and workflow_perm.can_approve:
                        has_authority = True
                        break
                    elif authority_type == 'reject' and workflow_perm.can_reject:
                        has_authority = True
                        break
                    elif authority_type == 'escalate' and workflow_perm.can_escalate:
                        has_authority = True
                        break
                    elif authority_type == 'override' and workflow_perm.can_override:
                        has_authority = True
                        break
            
            if not has_authority:
                abort(403)
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator
