"""
Template-based role management services

Provides template-based role management, sidebar access control, and role assignment helpers.
"""

from .role_template_service import RoleTemplateService, RoleTemplateManager
from .sidebar_access_service import SidebarAccessService
from .role_assignment_helpers import (
    assign_role_to_user,
    assign_predefined_role_to_user,
    get_user_role_level,
    can_manage_user,
    get_available_roles_for_assignment,
    assign_template_permissions_to_role,
    remove_role_from_user,
    transfer_user_to_role,
)

__all__ = [
    'RoleTemplateService',
    'RoleTemplateManager',
    'SidebarAccessService',
    'assign_role_to_user',
    'assign_predefined_role_to_user',
    'get_user_role_level',
    'can_manage_user',
    'get_available_roles_for_assignment',
    'assign_template_permissions_to_role',
    'remove_role_from_user',
    'transfer_user_to_role',
]
