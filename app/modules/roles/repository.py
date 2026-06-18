from sqlalchemy import func, and_, or_

from app.extensions import db
from app.modules.auth.models import Role, Permission, User, user_roles
from app.modules.roles.models import (
    WorkflowPermission,
    RoleHierarchy,
    ScopeType,
    RoleScope,
    ModuleAccess,
    RoleAuditLog,
    PermissionGroup,
)


class RolesRepository:
    """Repository for roles and access control data access"""

    def get_all_roles(self, filters=None, offset=0, limit=50):
        """Get all roles with optional filtering and pagination"""
        query = Role.query.order_by(Role.name)
        
        if filters:
            if filters.get('search'):
                search_val = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Role.name.ilike(search_val),
                        Role.description.ilike(search_val),
                    )
                )
            if filters.get('is_system') is not None:
                is_system_value = filters['is_system']
                if isinstance(is_system_value, str):
                    is_system_value = is_system_value.lower() in ['1', 'true', 'yes', 'y', 'on']
                query = query.filter(Role.is_system == is_system_value)
        
        total = query.count()
        roles = query.offset(offset).limit(limit).all()
        return roles, total

    def get_role_by_id(self, role_id):
        """Get a role with all related data"""
        return Role.query.get(role_id)

    def get_role_by_name(self, name):
        """Get a role by name"""
        return Role.query.filter_by(name=name).first()

    def get_role_hierarchy(self, role_id):
        """Get hierarchy info for a role"""
        return RoleHierarchy.query.filter_by(role_id=role_id).first()

    def get_role_permissions(self, role_id):
        """Get all permissions assigned to a role"""
        role = Role.query.get(role_id)
        if not role:
            return []
        return role.permissions

    def get_role_workflow_permissions(self, role_id):
        """Get workflow authorities for a role"""
        return WorkflowPermission.query.filter_by(role_id=role_id).all()

    def get_role_module_access(self, role_id):
        """Get module-level access matrix for a role"""
        return ModuleAccess.query.filter_by(role_id=role_id).all()

    def get_role_scopes(self, role_id):
        """Get accessible scopes for a role"""
        return RoleScope.query.filter_by(role_id=role_id).all()

    def get_role_users_count(self, role_id):
        """Get count of users with this role"""
        return (
            db.session.query(func.count(User.id))
            .join(user_roles)
            .filter(user_roles.c.role_id == role_id)
            .scalar() or 0
        )

    def get_hierarchy_levels(self):
        """Get all hierarchy levels"""
        return RoleHierarchy.query.order_by(RoleHierarchy.level).all()

    def get_hierarchy_by_level(self, level):
        """Get hierarchy by level"""
        return RoleHierarchy.query.filter_by(level=level).first()

    def get_scope_types(self, active_only=True):
        """Get all scope types"""
        query = ScopeType.query.order_by(ScopeType.level)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()

    def get_permission_groups(self, category=None):
        """Get permission groups"""
        query = PermissionGroup.query.filter_by(is_active=True)
        if category:
            query = query.filter_by(category=category)
        return query.order_by(PermissionGroup.name).all()

    def get_permissions_by_group(self, group_id):
        """Get all permissions in a group"""
        group = PermissionGroup.query.get(group_id)
        if not group:
            return []
        return group.permissions

    def count_total_roles(self):
        """Count total roles"""
        return Role.query.count()

    def count_active_roles(self):
        """Count active roles (has users assigned)"""
        return (
            db.session.query(func.count(Role.id.distinct()))
            .join(user_roles)
            .scalar() or 0
        )

    def count_total_permissions(self):
        """Count total permissions"""
        return Permission.query.count()

    def count_permission_groups(self):
        """Count permission groups"""
        return PermissionGroup.query.filter_by(is_active=True).count()

    def count_workflow_roles(self):
        """Count roles with workflow permissions"""
        return (
            db.session.query(func.count(WorkflowPermission.role_id.distinct()))
            .scalar() or 0
        )

    def count_restricted_roles(self):
        """Count roles with restricted access"""
        return (
            db.session.query(func.count(Role.id))
            .filter(Role.is_system == False)
            .scalar() or 0
        )

    def get_role_permissions_matrix(self, role_id):
        """Get complete module access matrix for a role"""
        module_access = ModuleAccess.query.filter_by(role_id=role_id).all()
        return {
            access.module_name: {
                'view': access.can_view,
                'create': access.can_create,
                'edit': access.can_edit,
                'delete': access.can_delete,
                'approve': access.can_approve,
                'export': access.can_export,
                'assign': access.can_assign,
            }
            for access in module_access
        }

    def create_role(self, name, description=None, is_system=False):
        """Create a new role"""
        role = Role(name=name, description=description, is_system=is_system)
        db.session.add(role)
        db.session.commit()
        return role

    def update_role(self, role_id, **kwargs):
        """Update a role"""
        role = Role.query.get(role_id)
        if not role:
            return None
        
        for key, value in kwargs.items():
            if hasattr(role, key) and key not in ['id', 'created_at']:
                setattr(role, key, value)
        
        db.session.commit()
        return role

    def add_permission_to_role(self, role_id, permission_id):
        """Add a permission to a role"""
        role = Role.query.get(role_id)
        permission = Permission.query.get(permission_id)
        
        if role and permission and permission not in role.permissions:
            role.permissions.append(permission)
            db.session.commit()
            return True
        return False

    def remove_permission_from_role(self, role_id, permission_id):
        """Remove a permission from a role"""
        role = Role.query.get(role_id)
        permission = Permission.query.get(permission_id)
        
        if role and permission and permission in role.permissions:
            role.permissions.remove(permission)
            db.session.commit()
            return True
        return False

    def set_module_access(self, role_id, module_name, access_dict):
        """Set module access for a role"""
        access = ModuleAccess.query.filter_by(role_id=role_id, module_name=module_name).first()
        
        if not access:
            access = ModuleAccess(role_id=role_id, module_name=module_name)
            db.session.add(access)
        
        for key, value in access_dict.items():
            if hasattr(access, key) and key.startswith('can_'):
                setattr(access, key, value)
        
        db.session.commit()
        return access

    def create_role_scope(self, role_id, scope_type_id):
        """Create scope assignment for a role"""
        scope = RoleScope(role_id=role_id, scope_type_id=scope_type_id)
        db.session.add(scope)
        db.session.commit()
        return scope

    def set_workflow_permission(self, role_id, workflow_type, permissions_dict):
        """Set workflow permissions for a role"""
        perm = WorkflowPermission.query.filter_by(role_id=role_id, workflow_type=workflow_type).first()
        
        if not perm:
            perm = WorkflowPermission(role_id=role_id, workflow_type=workflow_type)
            db.session.add(perm)
        
        for key, value in permissions_dict.items():
            if hasattr(perm, key) and key.startswith('can_'):
                setattr(perm, key, value)
        
        db.session.commit()
        return perm

    def get_role_audit_logs(self, role_id=None, limit=50):
        """Get audit logs for role changes"""
        query = RoleAuditLog.query.order_by(RoleAuditLog.created_at.desc())
        if role_id:
            query = query.filter_by(role_id=role_id)
        return query.limit(limit).all()

    def create_audit_log(self, role_id=None, action=None, entity_type=None, entity_id=None, 
                        old_value=None, new_value=None, user_id=None, ip_address=None):
        """Create an audit log entry"""
        log = RoleAuditLog(
            role_id=role_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            changed_by_user_id=user_id,
            ip_address=ip_address,
        )
        db.session.add(log)
        db.session.commit()
        return log

    def compare_roles(self, role_id_1, role_id_2):
        """Compare two roles' permissions and capabilities"""
        role1 = self.get_role_by_id(role_id_1)
        role2 = self.get_role_by_id(role_id_2)
        
        if not role1 or not role2:
            return None
        
        return {
            'role1': {
                'name': role1.name,
                'permissions': [p.name for p in role1.permissions],
                'module_access': self.get_role_permissions_matrix(role_id_1),
            },
            'role2': {
                'name': role2.name,
                'permissions': [p.name for p in role2.permissions],
                'module_access': self.get_role_permissions_matrix(role_id_2),
            }
        }
