"""
Permission Service Layer

Business logic for permission management, authorization, and access control
"""

from datetime import datetime, timezone
from flask_login import current_user

from app.extensions import db
from app.modules.auth.models import Permission, Role
from app.modules.permissions.models import (
    PermissionDetail,
    PermissionWorkflowAccess,
    PermissionCategory,
    PermissionAuditLog,
)
from app.modules.permissions.repository import PermissionRepository


class PermissionService:
    """Service for permission management"""

    def __init__(self):
        self.repository = PermissionRepository()

    # Dashboard operations

    def get_dashboard_kpis(self):
        """Get KPI data for permissions dashboard"""
        stats = self.repository.get_permission_statistics()
        
        return {
            'total_permissions': stats['total_permissions'],
            'active_permissions': stats['active_permissions'],
            'permission_groups': stats['total_categories'],
            'workflow_permissions': PermissionWorkflowAccess.query.count(),
            'restricted_permissions': PermissionDetail.query.filter_by(security_level='critical').count(),
            'assigned_roles': Role.query.count(),
        }

    # Permission management operations

    def create_permission(self, data):
        """Create a new permission with extended details"""
        try:
            # Create base permission
            permission = Permission(
                name=data.get('code'),
                description=data.get('description'),
            )
            db.session.add(permission)
            db.session.flush()

            # Create permission detail
            detail = PermissionDetail(
                permission_id=permission.id,
                module=data.get('module'),
                action=data.get('action'),
                scope_type=data.get('scope_type', 'global'),
                security_level=data.get('security_level', 'medium'),
                is_active=data.get('is_active', True),
                can_delegate=data.get('can_delegate', False),
                requires_mfa=data.get('requires_mfa', False),
                created_by=str(current_user.id) if current_user else None,
            )
            db.session.add(detail)

            # Create workflow access if provided
            if data.get('workflow_access'):
                workflow_access = PermissionWorkflowAccess(
                    permission_id=permission.id,
                    workflow_type=data['workflow_access'].get('workflow_type'),
                    can_approve=data['workflow_access'].get('can_approve', False),
                    can_reject=data['workflow_access'].get('can_reject', False),
                    can_escalate=data['workflow_access'].get('can_escalate', False),
                    can_override=data['workflow_access'].get('can_override', False),
                    can_close_workflow=data['workflow_access'].get('can_close_workflow', False),
                    approval_level=data['workflow_access'].get('approval_level', 0),
                )
                db.session.add(workflow_access)

            # Add to category if provided
            if data.get('category_id'):
                category = PermissionCategory.query.get(data['category_id'])
                if category:
                    permission.category = category

            db.session.commit()

            # Audit log
            self.repository.audit_permission_change(
                permission_id=permission.id,
                action='permission_created',
                entity_type='permission',
                new_value=data,
                status='success',
                severity='info'
            )

            return permission, None

        except Exception as e:
            db.session.rollback()
            return None, str(e)

    def update_permission(self, permission_id, data):
        """Update permission details"""
        try:
            permission = Permission.query.get(permission_id)
            if not permission:
                return None, "Permission not found"

            old_value = {
                'name': permission.name,
                'description': permission.description,
            }

            # Update base permission
            if 'description' in data:
                permission.description = data['description']

            # Update detail
            detail = permission.detail if hasattr(permission, 'detail') else None
            if detail:
                if 'scope_type' in data:
                    detail.scope_type = data['scope_type']
                if 'security_level' in data:
                    detail.security_level = data['security_level']
                if 'is_active' in data:
                    detail.is_active = data['is_active']
                if 'can_delegate' in data:
                    detail.can_delegate = data['can_delegate']
                if 'requires_mfa' in data:
                    detail.requires_mfa = data['requires_mfa']
                detail.updated_at = datetime.now(timezone.utc)

            db.session.commit()

            # Audit log
            self.repository.audit_permission_change(
                permission_id=permission_id,
                action='permission_updated',
                entity_type='permission',
                old_value=old_value,
                new_value=data,
                status='success',
                severity='info'
            )

            return permission, None

        except Exception as e:
            db.session.rollback()
            return None, str(e)

    def delete_permission(self, permission_id):
        """Soft delete a permission"""
        try:
            permission = Permission.query.get(permission_id)
            if not permission:
                return False, "Permission not found"

            detail = permission.detail if hasattr(permission, 'detail') else None
            if detail:
                detail.is_active = False
                detail.updated_at = datetime.now(timezone.utc)

            db.session.commit()

            # Audit log
            self.repository.audit_permission_change(
                permission_id=permission_id,
                action='permission_deleted',
                entity_type='permission',
                status='success',
                severity='warning'
            )

            return True, None

        except Exception as e:
            db.session.rollback()
            return False, str(e)

    # Role-Permission operations

    def get_role_permissions_grouped(self, role_id):
        """Get role permissions grouped by module"""
        role = Role.query.get(role_id)
        if not role:
            return {}

        grouped = {}
        for perm in role.permissions:
            detail = perm.detail if hasattr(perm, 'detail') and perm.detail else None
            if detail:
                module = detail.module
                if module not in grouped:
                    grouped[module] = []
                grouped[module].append({
                    'id': perm.id,
                    'name': perm.name,
                    'action': detail.action,
                    'scope_type': detail.scope_type,
                    'security_level': detail.security_level,
                })

        return grouped

    def assign_permission_to_role(self, role_id, permission_id):
        """Assign a permission to a role"""
        return self.repository.assign_permission_to_role(role_id, permission_id)

    def revoke_permission_from_role(self, role_id, permission_id):
        """Revoke a permission from a role"""
        return self.repository.revoke_permission_from_role(role_id, permission_id)

    def assign_permissions_bulk(self, role_id, permission_ids):
        """Assign multiple permissions to a role"""
        try:
            role = Role.query.get(role_id)
            if not role:
                return False, "Role not found"

            for permission_id in permission_ids:
                self.assign_permission_to_role(role_id, permission_id)

            return True, None

        except Exception as e:
            db.session.rollback()
            return False, str(e)

    def revoke_permissions_bulk(self, role_id, permission_ids):
        """Revoke multiple permissions from a role"""
        try:
            role = Role.query.get(role_id)
            if not role:
                return False, "Role not found"

            for permission_id in permission_ids:
                self.revoke_permission_from_role(role_id, permission_id)

            return True, None

        except Exception as e:
            db.session.rollback()
            return False, str(e)

    # Permission Matrix operations

    def get_permission_matrix(self, module=None, role_id=None):
        """Get permission matrix for display"""
        # Define all standard actions
        standard_actions = ['view', 'create', 'edit', 'delete', 'approve', 'export', 'assign', 'block', 'override']

        # Get all modules if not specified
        if not module:
            modules_query = db.session.query(PermissionDetail.module).distinct().all()
            modules = [m[0] for m in modules_query]
        else:
            modules = [module]

        role = Role.query.get(role_id) if role_id else None
        matrix = {}
        for mod in modules:
            matrix[mod] = {}
            for action in standard_actions:
                permission = Permission.query.join(
                    PermissionDetail
                ).filter(
                    PermissionDetail.module == mod,
                    PermissionDetail.action == action
                ).first()

                if permission:
                    has_perm = False
                    if role:
                        has_perm = permission in role.permissions

                    matrix[mod][action] = {
                        'id': permission.id,
                        'name': permission.name,
                        'assigned': has_perm,
                        'security_level': permission.detail.security_level if permission.detail else 'medium',
                    }
                else:
                    matrix[mod][action] = None

        return matrix

    # Category operations

    def get_all_categories(self):
        """Get all permission categories"""
        return self.repository.get_all_categories()

    def create_category(self, data):
        """Create a new permission category"""
        try:
            category = PermissionCategory(
                name=data['name'],
                code=data['code'],
                description=data.get('description'),
                icon=data.get('icon'),
                display_order=data.get('display_order', 0),
                is_active=True,
            )
            db.session.add(category)
            db.session.commit()
            return category, None

        except Exception as e:
            db.session.rollback()
            return None, str(e)

    # Analytics operations

    def get_permission_analytics(self):
        """Get detailed permission analytics"""
        stats = self.repository.get_permission_statistics()
        
        return {
            'total_permissions': stats['total_permissions'],
            'active_permissions': stats['active_permissions'],
            'total_categories': stats['total_categories'],
            'security_levels': stats['security_levels'],
            'modules': stats['modules'],
        }

    def get_role_permission_analytics(self, role_id):
        """Get analytics for a specific role"""
        return self.repository.get_role_permission_analytics(role_id)

    # Audit operations

    def get_recent_audit_logs(self, limit=50):
        """Get recent audit logs"""
        logs, _ = self.repository.get_audit_logs(limit=limit)
        return logs

    # Search and filter operations

    def search_permissions(self, query, skip=0, limit=50):
        """Search permissions"""
        return self.repository.search_permissions(query, skip, limit)

    def filter_permissions(self, filters, skip=0, limit=50):
        """Filter permissions by various criteria"""
        query = Permission.query

        if filters.get('module'):
            query = query.join(PermissionDetail).filter(PermissionDetail.module == filters['module'])

        if filters.get('action'):
            query = query.join(PermissionDetail).filter(PermissionDetail.action == filters['action'])

        if filters.get('security_level'):
            query = query.join(PermissionDetail).filter(PermissionDetail.security_level == filters['security_level'])

        if filters.get('status'):
            query = query.join(PermissionDetail).filter(PermissionDetail.is_active == (filters['status'] == 'active'))

        total = query.count()
        permissions = query.offset(skip).limit(limit).all()

        return permissions, total
