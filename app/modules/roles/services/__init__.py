"""
Roles Services - Unified exports for both RolesService and Template-based services

This module bridges the gap between the original RolesService (in services.py)
and the new template-based services. It provides imports from both.
"""

import importlib.util
import os

# Import template-based services from parent directory's template_services module
from app.modules.roles.template_services.role_template_service import RoleTemplateService, RoleTemplateManager
from app.modules.roles.template_services.sidebar_access_service import SidebarAccessService
from app.modules.roles.template_services.role_assignment_helpers import (
    assign_role_to_user,
    assign_predefined_role_to_user,
    get_user_role_level,
    can_manage_user,
    get_available_roles_for_assignment,
    assign_template_permissions_to_role,
    remove_role_from_user,
    transfer_user_to_role,
)

# Import RolesService from the original services.py module
# We need to load it directly using importlib to avoid circular imports caused by directory shadowing
services_module_path = os.path.join(os.path.dirname(__file__), '..', 'services.py')
spec = importlib.util.spec_from_file_location("roles_services_original", services_module_path)
_original_services = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_original_services)
RolesService = _original_services.RolesService

__all__ = [
    'RolesService',
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

