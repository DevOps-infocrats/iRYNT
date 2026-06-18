"""
Permissions Seed Data

Seed data for standard permissions in the system
"""

from datetime import datetime, timezone
from app.extensions import db
from app.modules.auth.models import Permission
from app.modules.permissions.models import (
    PermissionDetail,
    PermissionCategory,
)


def seed_permissions():
    """Seed standard permissions into the database"""
    
    # Create permission categories
    categories = [
        {
            'name': 'User Management',
            'code': 'users',
            'icon': 'bi-people',
            'display_order': 1,
        },
        {
            'name': 'Company Management',
            'code': 'companies',
            'icon': 'bi-building',
            'display_order': 2,
        },
        {
            'name': 'Circle Management',
            'code': 'circles',
            'icon': 'bi-diagram-3',
            'display_order': 3,
        },
        {
            'name': 'Client Management',
            'code': 'clients',
            'icon': 'bi-person-check',
            'display_order': 4,
        },
        {
            'name': 'Project Management',
            'code': 'projects',
            'icon': 'bi-kanban',
            'display_order': 5,
        },
        {
            'name': 'Vehicle Operations',
            'code': 'vehicles',
            'icon': 'bi-truck',
            'display_order': 6,
        },
        {
            'name': 'Deployments',
            'code': 'deployments',
            'icon': 'bi-rocket',
            'display_order': 7,
        },
        {
            'name': 'Attendance',
            'code': 'attendance',
            'icon': 'bi-calendar-check',
            'display_order': 8,
        },
        {
            'name': 'Reports & Analytics',
            'code': 'reports',
            'icon': 'bi-graph-up',
            'display_order': 9,
        },
        {
            'name': 'Permissions',
            'code': 'permissions',
            'icon': 'bi-shield-check',
            'display_order': 10,
        },
        {
            'name': 'Notifications',
            'code': 'notifications',
            'icon': 'bi-bell',
            'display_order': 11,
        },
    ]

    # Standard permissions for each module
    permissions_data = [
        # User permissions
        ('users.view', 'View Users', 'users', 'view', 'global', 'low'),
        ('users.create', 'Create User', 'users', 'create', 'global', 'medium'),
        ('users.edit', 'Edit User', 'users', 'edit', 'global', 'medium'),
        ('users.delete', 'Delete User', 'users', 'delete', 'global', 'critical'),
        ('users.block', 'Block User', 'users', 'block', 'global', 'critical'),
        ('users.export', 'Export Users', 'users', 'export', 'global', 'medium'),

        # Company permissions
        ('companies.view', 'View Companies', 'companies', 'view', 'global', 'low'),
        ('companies.create', 'Create Company', 'companies', 'create', 'global', 'critical'),
        ('companies.edit', 'Edit Company', 'companies', 'edit', 'company', 'medium'),
        ('companies.delete', 'Delete Company', 'companies', 'delete', 'global', 'critical'),

        # Circle permissions
        ('circles.view', 'View Circles', 'circles', 'view', 'company', 'low'),
        ('circles.create', 'Create Circle', 'circles', 'create', 'company', 'medium'),
        ('circles.edit', 'Edit Circle', 'circles', 'edit', 'circle', 'medium'),
        ('circles.delete', 'Delete Circle', 'circles', 'delete', 'company', 'critical'),

        # Client permissions
        ('clients.view', 'View Clients', 'clients', 'view', 'circle', 'low'),
        ('clients.create', 'Create Client', 'clients', 'create', 'circle', 'medium'),
        ('clients.edit', 'Edit Client', 'clients', 'edit', 'client', 'medium'),
        ('clients.delete', 'Delete Client', 'clients', 'delete', 'circle', 'critical'),

        # Project permissions
        ('projects.view', 'View Projects', 'projects', 'view', 'client', 'low'),
        ('projects.create', 'Create Project', 'projects', 'create', 'client', 'medium'),
        ('projects.edit', 'Edit Project', 'projects', 'edit', 'project', 'medium'),
        ('projects.delete', 'Delete Project', 'projects', 'delete', 'client', 'critical'),

        # Vehicle permissions
        ('vehicles.view', 'View Vehicles', 'vehicles', 'view', 'project', 'low'),
        ('vehicles.create', 'Create Vehicle', 'vehicles', 'create', 'project', 'medium'),
        ('vehicles.edit', 'Edit Vehicle', 'vehicles', 'edit', 'project', 'medium'),
        ('vehicles.delete', 'Delete Vehicle', 'vehicles', 'delete', 'project', 'critical'),
        ('vehicles.assign', 'Assign Vehicle', 'vehicles', 'assign', 'project', 'medium'),
        ('vehicles.block', 'Block Vehicle', 'vehicles', 'block', 'project', 'medium'),

        # Deployment permissions
        ('deployments.view', 'View Deployments', 'deployments', 'view', 'project', 'low'),
        ('deployments.create', 'Create Deployment', 'deployments', 'create', 'project', 'medium'),
        ('deployments.edit', 'Edit Deployment', 'deployments', 'edit', 'project', 'medium'),
        ('deployments.delete', 'Delete Deployment', 'deployments', 'delete', 'project', 'critical'),
        ('deployments.approve', 'Approve Deployment', 'deployments', 'approve', 'project', 'critical'),
        ('helper_assignments.view', 'View Helper Assignments', 'deployments', 'view', 'project', 'low'),
        ('helper_assignments.create', 'Create Helper Assignment', 'deployments', 'create', 'project', 'medium'),
        ('helper_assignments.edit', 'Edit Helper Assignment', 'deployments', 'edit', 'project', 'medium'),
        ('helper_assignments.delete', 'Delete Helper Assignment', 'deployments', 'delete', 'project', 'critical'),

        # Attendance permissions
        ('attendance.view', 'View Attendance', 'attendance', 'view', 'project', 'low'),
        ('attendance.mark', 'Mark Attendance', 'attendance', 'mark', 'project', 'medium'),
        ('attendance.approve', 'Approve Attendance', 'attendance', 'approve', 'project', 'medium'),
        ('attendance.export', 'Export Attendance', 'attendance', 'export', 'project', 'medium'),

        # Reports permissions
        ('reports.view', 'View Reports', 'reports', 'view', 'project', 'low'),
        ('reports.export', 'Export Reports', 'reports', 'export', 'project', 'medium'),
        ('reports.analytics', 'View Analytics', 'reports', 'view', 'project', 'medium'),

        # Permissions permissions
        ('permissions.view', 'View Permissions', 'permissions', 'view', 'global', 'low'),
        ('permissions.create', 'Create Permission', 'permissions', 'create', 'global', 'critical'),
        ('permissions.edit', 'Edit Permission', 'permissions', 'edit', 'global', 'critical'),
        ('permissions.delete', 'Delete Permission', 'permissions', 'delete', 'global', 'critical'),
        ('permissions.assign', 'Assign Permission', 'permissions', 'assign', 'global', 'critical'),
        ('permissions.revoke', 'Revoke Permission', 'permissions', 'revoke', 'global', 'critical'),
        ('permissions.view_audit', 'View Audit Logs', 'permissions', 'view', 'global', 'medium'),
        ('permissions.manage_settings', 'Manage Settings', 'permissions', 'edit', 'global', 'critical'),
        ('permissions.manage_roles', 'Manage Roles', 'permissions', 'edit', 'global', 'critical'),

        # Notifications permissions
        ('notifications.view', 'View Notifications', 'notifications', 'view', 'global', 'low'),
    ]

    # Add categories
    for cat_data in categories:
        existing = PermissionCategory.query.filter_by(code=cat_data['code']).first()
        if not existing:
            category = PermissionCategory(**cat_data)
            db.session.add(category)

    db.session.flush()

    # Add permissions
    for perm_code, perm_name, module, action, scope, security in permissions_data:
        existing = Permission.query.filter_by(name=perm_code).first()
        if not existing:
            permission = Permission(
                name=perm_code,
                description=perm_name,
            )
            db.session.add(permission)
            db.session.flush()

            category = PermissionCategory.query.filter_by(code=module).first()
            
            detail = PermissionDetail(
                permission_id=permission.id,
                module=module,
                action=action,
                scope_type=scope,
                security_level=security,
                is_active=True,
            )
            db.session.add(detail)

            if category:
                permission.category_id = category.id

    db.session.commit()


if __name__ == '__main__':
    from app import create_app
    
    app = create_app()
    with app.app_context():
        seed_permissions()
        print("✅ Permissions seeded successfully!")
