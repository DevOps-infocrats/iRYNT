"""
Permission Validators

Validation functions for permission operations
"""

import re
from app.modules.auth.models import Permission, Role


class PermissionValidator:
    """Validator for permission operations"""

    @staticmethod
    def validate_permission_code(code):
        """Validate permission code format (module.action)"""
        pattern = r'^[a-z_]+\.[a-z_]+$'
        if not re.match(pattern, code):
            return False, "Permission code must be in format 'module.action' (lowercase letters and underscores only)"
        return True, None

    @staticmethod
    def validate_permission_uniqueness(code, exclude_id=None):
        """Check if permission code is unique"""
        query = Permission.query.filter_by(name=code)
        if exclude_id:
            query = query.filter(Permission.id != exclude_id)
        
        if query.first():
            return False, "Permission code already exists"
        return True, None

    @staticmethod
    def validate_module_name(module):
        """Validate module name"""
        if not module or not isinstance(module, str) or len(module) < 1 or len(module) > 120:
            return False, "Invalid module name"
        return True, None

    @staticmethod
    def validate_action_type(action):
        """Validate action type"""
        valid_actions = [
            'view', 'create', 'edit', 'delete', 'approve', 
            'reject', 'export', 'import', 'assign', 'block', 
            'override', 'escalate', 'close', 'manage'
        ]
        if action not in valid_actions:
            return False, f"Invalid action. Must be one of: {', '.join(valid_actions)}"
        return True, None

    @staticmethod
    def validate_scope_type(scope_type):
        """Validate scope type"""
        valid_scopes = ['global', 'company', 'circle', 'client', 'project', 'subzone', 'operational']
        if scope_type not in valid_scopes:
            return False, f"Invalid scope type. Must be one of: {', '.join(valid_scopes)}"
        return True, None

    @staticmethod
    def validate_security_level(level):
        """Validate security level"""
        valid_levels = ['low', 'medium', 'critical']
        if level not in valid_levels:
            return False, f"Invalid security level. Must be one of: {', '.join(valid_levels)}"
        return True, None

    @staticmethod
    def validate_role_id(role_id):
        """Validate role exists"""
        role = Role.query.filter_by(id=role_id).first()
        if not role:
            return False, "Role not found"
        return True, None

    @staticmethod
    def validate_permission_id(permission_id):
        """Validate permission exists"""
        permission = Permission.query.filter_by(id=permission_id).first()
        if not permission:
            return False, "Permission not found"
        return True, None

    @staticmethod
    def validate_permission_data(data):
        """Validate complete permission data"""
        errors = []

        # Validate code
        if 'code' in data:
            valid, error = PermissionValidator.validate_permission_code(data['code'])
            if not valid:
                errors.append(error)

        # Validate module
        if 'module' in data:
            valid, error = PermissionValidator.validate_module_name(data['module'])
            if not valid:
                errors.append(error)

        # Validate action
        if 'action' in data:
            valid, error = PermissionValidator.validate_action_type(data['action'])
            if not valid:
                errors.append(error)

        # Validate scope type
        if 'scope_type' in data:
            valid, error = PermissionValidator.validate_scope_type(data['scope_type'])
            if not valid:
                errors.append(error)

        # Validate security level
        if 'security_level' in data:
            valid, error = PermissionValidator.validate_security_level(data['security_level'])
            if not valid:
                errors.append(error)

        return len(errors) == 0, errors

    @staticmethod
    def validate_role_permission_assignment(role_id, permission_id):
        """Validate role-permission assignment"""
        errors = []

        # Check role exists
        valid, error = PermissionValidator.validate_role_id(role_id)
        if not valid:
            errors.append(error)

        # Check permission exists
        valid, error = PermissionValidator.validate_permission_id(permission_id)
        if not valid:
            errors.append(error)

        # Check if not already assigned
        if not errors:
            role = Role.query.get(role_id)
            permission = Permission.query.get(permission_id)
            if permission in role.permissions:
                errors.append("Permission is already assigned to this role")

        return len(errors) == 0, errors
