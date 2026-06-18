from app.modules.roles.repository import RolesRepository


class RolesService:
    """Business logic for roles and access control"""

    def __init__(self):
        self.repository = RolesRepository()

    def get_dashboard_kpis(self):
        """Get KPI metrics for roles dashboard"""
        return [
            {
                'title': 'Total Roles',
                'value': self.repository.count_total_roles(),
                'icon': 'security',
                'trend': '+5%',
                'description': 'Active roles in system'
            },
            {
                'title': 'Active Roles',
                'value': self.repository.count_active_roles(),
                'icon': 'verified_user',
                'trend': '+12%',
                'description': 'Roles with assignments'
            },
            {
                'title': 'Permission Groups',
                'value': self.repository.count_permission_groups(),
                'icon': 'category',
                'trend': '+3%',
                'description': 'Grouped permissions'
            },
            {
                'title': 'Workflow Roles',
                'value': self.repository.count_workflow_roles(),
                'icon': 'workflow',
                'trend': '+8%',
                'description': 'With approval rights'
            },
            {
                'title': 'Restricted Roles',
                'value': self.repository.count_restricted_roles(),
                'icon': 'lock',
                'trend': '+2%',
                'description': 'Limited access roles'
            },
            {
                'title': 'Permissions',
                'value': self.repository.count_total_permissions(),
                'icon': 'shield',
                'trend': '+18%',
                'description': 'Total permissions defined'
            }
        ]

    def list_roles(self, filters=None, page=1, per_page=50):
        """Get paginated list of roles"""
        offset = (page - 1) * per_page
        roles, total = self.repository.get_all_roles(filters, offset, per_page)
        
        return {
            'roles': [self._serialize_role(role) for role in roles],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }

    def get_role_detail(self, role_id):
        """Get complete role details with all related data"""
        role = self.repository.get_role_by_id(role_id)
        if not role:
            return None
        
        hierarchy = self.repository.get_role_hierarchy(role_id)
        permissions = self.repository.get_role_permissions(role_id)
        workflows = self.repository.get_role_workflow_permissions(role_id)
        modules = self.repository.get_role_module_access(role_id)
        scopes = self.repository.get_role_scopes(role_id)
        users_count = self.repository.get_role_users_count(role_id)
        audit_logs = self.repository.get_role_audit_logs(role_id, limit=10)
        
        return {
            'id': role.id,
            'name': role.name,
            'description': role.description,
            'is_system': role.is_system,
            'created_at': role.created_at.isoformat() if role.created_at else None,
            'updated_at': role.updated_at.isoformat() if role.updated_at else None,
            'hierarchy': {
                'level': hierarchy.level if hierarchy else None,
                'tier': hierarchy.tier if hierarchy else None,
                'parent_level': hierarchy.parent_level if hierarchy else None,
            } if hierarchy else None,
            'permissions': [{'id': p.id, 'name': p.name} for p in permissions],
            'permission_count': len(permissions),
            'workflows': [self._serialize_workflow_permission(w) for w in workflows],
            'modules': [self._serialize_module_access(m) for m in modules],
            'scopes': [{'scope_type': s.scope_type.name if s.scope_type else None} for s in scopes],
            'users_count': users_count,
            'audit_logs': [self._serialize_audit_log(log) for log in audit_logs],
        }

    def get_hierarchy_visualization(self):
        """Get role hierarchy data for visualization"""
        hierarchies = self.repository.get_hierarchy_levels()
        
        tiers = {
            'system': [],
            'corporate': [],
            'circle': [],
            'field': []
        }
        
        for h in hierarchies:
            role = self.repository.get_role_by_id(h.role_id)
            if role and h.tier in tiers:
                tiers[h.tier].append({
                    'level': h.level,
                    'role_name': role.name,
                    'role_id': role.id,
                    'parent_level': h.parent_level,
                    'description': h.description,
                })
        
        return tiers

    def get_permission_matrix(self, role_id):
        """Get module access matrix for a role"""
        modules = [
            'users', 'companies', 'circles', 'clients', 'projects',
            'subzones', 'vehicles', 'deployments', 'attendance',
            'reports', 'workflows', 'notifications', 'audit_logs'
        ]
        
        matrix = {}
        for module in modules:
            access = self.repository.get_role_module_access(role_id)
            module_access = next((a for a in access if a.module_name == module), None)
            
            if module_access:
                matrix[module] = {
                    'view': module_access.can_view,
                    'create': module_access.can_create,
                    'edit': module_access.can_edit,
                    'delete': module_access.can_delete,
                    'approve': module_access.can_approve,
                    'export': module_access.can_export,
                    'assign': module_access.can_assign,
                }
            else:
                matrix[module] = {
                    'view': False, 'create': False, 'edit': False,
                    'delete': False, 'approve': False, 'export': False, 'assign': False
                }
        
        return matrix

    def compare_roles(self, role_id_1, role_id_2):
        """Compare two roles"""
        return self.repository.compare_roles(role_id_1, role_id_2)

    def _serialize_role(self, role):
        """Serialize role for API response"""
        hierarchy = self.repository.get_role_hierarchy(role.id) if role else None
        permissions_count = len(role.permissions) if role else 0
        workflows_count = len(role.workflow_permissions) if hasattr(role, 'workflow_permissions') else 0
        users_count = self.repository.get_role_users_count(role.id) if role else 0
        
        return {
            'id': role.id,
            'name': role.name,
            'code': role.name.lower().replace(' ', '_'),
            'description': role.description,
            'level': hierarchy.level if hierarchy else None,
            'permissions_count': permissions_count,
            'workflow_count': workflows_count,
            'users_count': users_count,
            'is_system': role.is_system,
            'status': 'Active' if users_count > 0 else 'Inactive',
        }

    def _serialize_workflow_permission(self, workflow):
        """Serialize workflow permission"""
        return {
            'workflow_type': workflow.workflow_type,
            'can_approve': workflow.can_approve,
            'can_reject': workflow.can_reject,
            'can_escalate': workflow.can_escalate,
            'can_override': workflow.can_override,
            'can_close_workflow': workflow.can_close_workflow,
            'approval_level': workflow.approval_level,
        }

    def _serialize_module_access(self, access):
        """Serialize module access"""
        return {
            'module': access.module_name,
            'view': access.can_view,
            'create': access.can_create,
            'edit': access.can_edit,
            'delete': access.can_delete,
            'approve': access.can_approve,
            'export': access.can_export,
            'assign': access.can_assign,
        }

    def _serialize_audit_log(self, log):
        """Serialize audit log"""
        return {
            'action': log.action,
            'entity_type': log.entity_type,
            'timestamp': log.created_at.isoformat() if log.created_at else None,
        }
