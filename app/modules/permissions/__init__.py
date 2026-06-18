"""Permissions Management Module"""

from app.modules.permissions.models import (
    PermissionDetail,
    PermissionWorkflowAccess,
    PermissionCategory,
    PermissionAuditLog,
    PermissionScope,
    RolePermissionMatrix,
)

__all__ = [
    'PermissionDetail',
    'PermissionWorkflowAccess',
    'PermissionCategory',
    'PermissionAuditLog',
    'PermissionScope',
    'RolePermissionMatrix',
]
