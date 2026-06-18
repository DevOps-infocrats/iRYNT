"""
Permission Repository Layer

Data access layer for permissions, roles, and access control
"""

from datetime import datetime, timezone
from sqlalchemy import and_, or_, func, desc
from flask_login import current_user

from app.extensions import db
from app.modules.auth.models import Permission, Role
from app.modules.permissions.models import (
    PermissionDetail,
    PermissionWorkflowAccess,
    PermissionCategory,
    PermissionAuditLog,
    PermissionScope,
    RolePermissionMatrix,
)


class PermissionRepository:
    """Repository for permission operations"""

    def get_all_permissions(self, active_only=True, skip=0, limit=50):
        """Get all permissions with pagination"""
        query = Permission.query.outerjoin(PermissionDetail)
        if active_only:
            query = query.filter(PermissionDetail.is_active == True)

        total = query.count()
        permissions = query.offset(skip).limit(limit).all()

        return permissions, total

    def get_permission_by_id(self, permission_id):
        """Get permission by ID"""
        return Permission.query.filter_by(id=permission_id).first()

    def get_permission_by_code(self, code):
        """Get permission by code (module.action)"""
        return Permission.query.filter_by(name=code).first()

    def get_permissions_by_module(self, module, skip=0, limit=50):
        """Get all permissions for a specific module"""
        query = PermissionDetail.query.filter_by(module=module)
        total = query.count()
        permissions = query.offset(skip).limit(limit).all()
        return permissions, total

    def get_permissions_by_action(self, action, skip=0, limit=50):
        """Get all permissions for a specific action"""
        query = PermissionDetail.query.filter_by(action=action)
        total = query.count()
        permissions = query.offset(skip).limit(limit).all()
        return permissions, total

    def get_permissions_by_scope(self, scope_type, skip=0, limit=50):
        """Get permissions by scope type"""
        query = PermissionDetail.query.filter_by(scope_type=scope_type)
        total = query.count()
        permissions = query.offset(skip).limit(limit).all()
        return permissions, total

    def get_permissions_by_category(self, category_id, skip=0, limit=50):
        """Get permissions by category"""
        category = PermissionCategory.query.get(category_id)
        if not category:
            return [], 0
        
        query = category.permissions
        total = query.count()
        permissions = query.offset(skip).limit(limit).all()
        return permissions, total

    def get_permission_detail(self, permission_id):
        """Get extended permission details"""
        return PermissionDetail.query.filter_by(permission_id=permission_id).first()

    def get_permission_workflow_access(self, permission_id):
        """Get workflow access for a permission"""
        return PermissionWorkflowAccess.query.filter_by(permission_id=permission_id).first()

    def count_total_permissions(self):
        """Count total permissions"""
        return Permission.query.count()

    def count_active_permissions(self):
        """Count active permissions"""
        query = PermissionDetail.query.filter_by(is_active=True)
        return query.count()

    def count_permission_categories(self):
        """Count permission categories"""
        return PermissionCategory.query.filter_by(is_active=True).count()

    def get_all_categories(self, active_only=True):
        """Get all permission categories"""
        query = PermissionCategory.query
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(PermissionCategory.display_order).all()

    # Role-Permission operations

    def get_role_permissions(self, role_id, skip=0, limit=50):
        """Get all permissions assigned to a role"""
        role = Role.query.get(role_id)
        if not role:
            return [], 0

        total = len(role.permissions)
        permissions = role.permissions[skip:skip + limit]
        return permissions, total

    def assign_permission_to_role(self, role_id, permission_id):
        """Assign a permission to a role"""
        role = Role.query.get(role_id)
        permission = Permission.query.get(permission_id)

        if not role or not permission:
            return False

        if permission not in role.permissions:
            role.permissions.append(permission)
            
            # Create role permission matrix entry
            existing = RolePermissionMatrix.query.filter_by(
                role_id=role_id,
                permission_id=permission_id
            ).first()
            
            if not existing:
                matrix = RolePermissionMatrix(
                    role_id=role_id,
                    permission_id=permission_id,
                    assigned_by=str(current_user.id) if current_user else None,
                    assigned_at=datetime.now(timezone.utc)
                )
                db.session.add(matrix)
            
            # Log audit
            self.audit_permission_change(
                permission_id=permission_id,
                role_id=role_id,
                action='permission_assigned',
                status='success'
            )
            
            db.session.commit()
            return True

        return False

    def revoke_permission_from_role(self, role_id, permission_id):
        """Revoke a permission from a role"""
        role = Role.query.get(role_id)
        permission = Permission.query.get(permission_id)

        if not role or not permission:
            return False

        if permission in role.permissions:
            role.permissions.remove(permission)
            
            # Remove from matrix
            RolePermissionMatrix.query.filter_by(
                role_id=role_id,
                permission_id=permission_id
            ).delete()
            
            # Log audit
            self.audit_permission_change(
                permission_id=permission_id,
                role_id=role_id,
                action='permission_revoked',
                status='success'
            )
            
            db.session.commit()
            return True

        return False

    def has_permission(self, role_id, permission_code):
        """Check if a role has a specific permission"""
        role = Role.query.get(role_id)
        if not role:
            return False

        permission = Permission.query.filter_by(name=permission_code).first()
        if not permission:
            return False

        return permission in role.permissions

    def get_role_module_access(self, role_id):
        """Get module-level access for a role"""
        # Get all permissions for the role and group by module
        from app.modules.roles.models import ModuleAccess
        
        return ModuleAccess.query.filter_by(role_id=role_id).all()

    # Audit operations

    def audit_permission_change(
        self,
        permission_id=None,
        role_id=None,
        action='permission_change',
        entity_type='permission',
        status='success',
        old_value=None,
        new_value=None,
        ip_address=None,
        user_agent=None,
        severity='info'
    ):
        """Log permission audit event"""
        audit_log = PermissionAuditLog(
            permission_id=permission_id,
            role_id=role_id,
            user_id=str(current_user.id) if current_user else None,
            action=action,
            entity_type=entity_type,
            action_type='permission_change',
            status=status,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity,
        )
        db.session.add(audit_log)
        db.session.commit()
        return audit_log

    def get_audit_logs(self, skip=0, limit=50, role_id=None, permission_id=None):
        """Get audit logs with optional filtering"""
        query = PermissionAuditLog.query

        if role_id:
            query = query.filter_by(role_id=role_id)
        if permission_id:
            query = query.filter_by(permission_id=permission_id)

        total = query.count()
        logs = query.order_by(desc(PermissionAuditLog.created_at)).offset(skip).limit(limit).all()
        return logs, total

    # Analytics operations

    def get_permission_statistics(self):
        """Get permission analytics"""
        total_permissions = Permission.query.count()
        active_permissions = PermissionDetail.query.filter_by(is_active=True).count()
        total_categories = PermissionCategory.query.count()
        
        # Permissions by security level
        security_levels = db.session.query(
            PermissionDetail.security_level,
            func.count(PermissionDetail.id)
        ).group_by(PermissionDetail.security_level).all()

        # Permissions by module
        modules = db.session.query(
            PermissionDetail.module,
            func.count(PermissionDetail.id)
        ).group_by(PermissionDetail.module).all()

        return {
            'total_permissions': total_permissions,
            'active_permissions': active_permissions,
            'total_categories': total_categories,
            'security_levels': dict(security_levels),
            'modules': dict(modules),
        }

    def get_role_permission_analytics(self, role_id):
        """Get permission analytics for a role"""
        role = Role.query.get(role_id)
        if not role:
            return {}

        permissions = role.permissions

        # Group by module and action
        modules = {}
        for perm in permissions:
            detail = perm.detail if hasattr(perm, 'detail') and perm.detail else None
            if detail:
                module = detail.module
                if module not in modules:
                    modules[module] = []
                modules[module].append(detail.action)

        return {
            'total_permissions': len(permissions),
            'modules': modules,
            'module_count': len(modules),
        }

    # Cache-related operations

    def get_permission_code(self, module, action):
        """Generate permission code from module and action"""
        return f"{module}.{action}"

    def search_permissions(self, query, skip=0, limit=50):
        """Search permissions by name or description"""
        search_query = Permission.query.filter(
            or_(
                Permission.name.ilike(f'%{query}%'),
                Permission.description.ilike(f'%{query}%')
            )
        )

        total = search_query.count()
        permissions = search_query.offset(skip).limit(limit).all()
        return permissions, total
