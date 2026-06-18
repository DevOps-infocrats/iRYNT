"""
Idempotent Permission Seeding System

Seeds predefined enterprise permissions from a comprehensive permission matrix.
- Safe for multiple runs
- Creates permissions if not exist
- Updates existing permissions
- Preserves role-permission assignments
"""

from app.extensions import db
from app.modules.auth.models import Permission
from app.modules.permissions.models import PermissionCategory, PermissionDetail


# Comprehensive permission matrix
PERMISSION_MATRIX = {
    'User Management': {
        'icon': 'person',
        'permissions': [
            ('users.view', 'View users', 'medium'),
            ('users.create', 'Create users', 'medium'),
            ('users.edit', 'Edit users', 'medium'),
            ('users.delete', 'Delete users', 'critical'),
            ('users.block', 'Block/Unblock users', 'critical'),
            ('users.export', 'Export user data', 'medium'),
        ]
    },
    'Role Management': {
        'icon': 'security',
        'permissions': [
            ('roles.view', 'View roles', 'low'),
            ('roles.create', 'Create roles', 'critical'),
            ('roles.edit', 'Edit roles', 'critical'),
            ('roles.delete', 'Delete roles', 'critical'),
        ]
    },
    'Permission Management': {
        'icon': 'shield',
        'permissions': [
            ('permissions.view', 'View permissions', 'low'),
            ('permissions.create', 'Create permissions', 'critical'),
            ('permissions.edit', 'Edit permissions', 'critical'),
            ('permissions.delete', 'Delete permissions', 'critical'),
            ('permissions.assign', 'Assign permissions', 'critical'),
            ('permissions.audit', 'View permission audit', 'medium'),
        ]
    },
    'Company Management': {
        'icon': 'business',
        'permissions': [
            ('companies.view', 'View companies', 'low'),
            ('companies.create', 'Create companies', 'medium'),
            ('companies.edit', 'Edit companies', 'medium'),
            ('companies.delete', 'Delete companies', 'critical'),
        ]
    },
    'Circle Management': {
        'icon': 'public',
        'permissions': [
            ('circles.view', 'View circles', 'low'),
            ('circles.create', 'Create circles', 'medium'),
            ('circles.edit', 'Edit circles', 'medium'),
            ('circles.delete', 'Delete circles', 'critical'),
        ]
    },
    'Client Management': {
        'icon': 'handshake',
        'permissions': [
            ('clients.view', 'View clients', 'low'),
            ('clients.create', 'Create clients', 'medium'),
            ('clients.edit', 'Edit clients', 'medium'),
            ('clients.delete', 'Delete clients', 'critical'),
        ]
    },
    'Project Management': {
        'icon': 'work_outline',
        'permissions': [
            ('projects.view', 'View projects', 'low'),
            ('projects.create', 'Create projects', 'medium'),
            ('projects.edit', 'Edit projects', 'medium'),
            ('projects.delete', 'Delete projects', 'critical'),
            ('projects.approve', 'Approve projects', 'medium'),
        ]
    },
    'Vehicle Operations': {
        'icon': 'directions_bus',
        'permissions': [
            ('vehicles.view', 'View vehicles', 'low'),
            ('vehicles.create', 'Create vehicles', 'medium'),
            ('vehicles.edit', 'Edit vehicles', 'medium'),
            ('vehicles.delete', 'Delete vehicles', 'critical'),
            ('vehicles.assign', 'Assign vehicles', 'medium'),
            ('vehicles.block', 'Block vehicles', 'critical'),
        ]
    },
    'Deployments': {
        'icon': 'local_shipping',
        'permissions': [
            ('deployments.view', 'View deployments', 'low'),
            ('deployments.create', 'Create deployments', 'medium'),
            ('deployments.edit', 'Edit deployments', 'medium'),
            ('deployments.delete', 'Delete deployments', 'critical'),
            ('deployments.approve', 'Approve deployments', 'medium'),
            ('deployments.override', 'Override deployments', 'critical'),
            ('helper_assignments.view', 'View helper assignments', 'low'),
            ('helper_assignments.create', 'Create helper assignments', 'medium'),
            ('helper_assignments.edit', 'Edit helper assignments', 'medium'),
            ('helper_assignments.delete', 'Delete helper assignments', 'critical'),
        ]
    },
    'Attendance': {
        'icon': 'assignment',
        'permissions': [
            ('attendance.view', 'View attendance', 'low'),
            ('attendance.mark', 'Mark attendance', 'medium'),
            ('attendance.approve', 'Approve attendance', 'medium'),
            ('attendance.export', 'Export attendance', 'medium'),
            ('attendance.override', 'Override attendance', 'critical'),
        ]
    },
    'Reports & Analytics': {
        'icon': 'query_stats',
        'permissions': [
            ('reports.view', 'View reports', 'low'),
            ('reports.export', 'Export reports', 'medium'),
            ('reports.analytics', 'View analytics', 'low'),
        ]
    },
    'Workflows': {
        'icon': 'process_analytics',
        'permissions': [
            ('workflows.view', 'View workflows', 'low'),
            ('workflows.manage', 'Manage workflows', 'medium'),
            ('workflows.approve', 'Approve workflow actions', 'medium'),
        ]
    },
    'Access Control': {
        'icon': 'lock',
        'permissions': [
            ('access_control.view', 'View access control', 'low'),
            ('access_control.manage', 'Manage access control', 'critical'),
        ]
    },
    'Audit & Compliance': {
        'icon': 'audit',
        'permissions': [
            ('audit.view', 'View audit logs', 'medium'),
            ('audit.export', 'Export audit logs', 'medium'),
        ]
    },
    'Notifications': {
        'icon': 'notifications',
        'permissions': [
            ('notifications.view', 'View notifications', 'low'),
        ]
    },
    'System Administration': {
        'icon': 'admin_panel_settings',
        'permissions': [
            ('system.settings', 'System settings', 'critical'),
            ('system.maintenance', 'System maintenance', 'critical'),
        ]
    },
}


def seed_permission_categories():
    """Seed permission categories (idempotent)"""
    created = 0
    updated = 0
    
    display_order = 0
    for category_name, category_data in PERMISSION_MATRIX.items():
        existing = PermissionCategory.query.filter_by(name=category_name).first()
        
        if existing:
            # Update if needed
            existing.icon = category_data.get('icon')
            existing.display_order = display_order
            updated += 1
        else:
            # Create new
            category = PermissionCategory(
                name=category_name,
                code=category_name.lower().replace(' ', '_'),
                description=f'{category_name} permissions',
                icon=category_data.get('icon'),
                display_order=display_order,
                is_active=True
            )
            db.session.add(category)
            created += 1
        
        display_order += 1
    
    db.session.commit()
    return created, updated


def seed_permissions():
    """Seed predefined permissions (idempotent)"""
    created = 0
    updated = 0
    
    for category_name, category_data in PERMISSION_MATRIX.items():
        # Get category
        category = PermissionCategory.query.filter_by(name=category_name).first()
        if not category:
            print(f"Warning: Category '{category_name}' not found")
            continue
        
        # Create permissions
        for perm_code, perm_desc, perm_level in category_data['permissions']:
            existing = Permission.query.filter_by(name=perm_code).first()
            
            if existing:
                # Update if needed
                existing.description = perm_desc
                existing.category_id = category.id
                updated += 1
            else:
                # Create new
                permission = Permission(
                    name=perm_code,
                    description=perm_desc,
                    category_id=category.id
                )
                db.session.add(permission)
                created += 1
    
    db.session.commit()
    return created, updated


def seed_permission_details():
    """Seed permission details (extended metadata) (idempotent)"""
    created = 0
    updated = 0
    
    for category_name, category_data in PERMISSION_MATRIX.items():
        for perm_code, perm_desc, perm_level in category_data['permissions']:
            # Get permission
            permission = Permission.query.filter_by(name=perm_code).first()
            if not permission:
                continue
            
            # Check if detail exists
            existing = PermissionDetail.query.filter_by(permission_id=permission.id).first()
            
            # Parse module and action
            parts = perm_code.split('.')
            module = parts[0] if len(parts) > 0 else 'system'
            action = '.'.join(parts[1:]) if len(parts) > 1 else perm_code
            
            if existing:
                # Update if needed
                existing.module = module
                existing.action = action
                existing.security_level = perm_level
                updated += 1
            else:
                # Create new
                detail = PermissionDetail(
                    permission_id=permission.id,
                    module=module,
                    action=action,
                    scope_type='global',
                    security_level=perm_level,
                    is_active=True,
                    can_delegate=False,
                    requires_mfa=perm_level == 'critical'
                )
                db.session.add(detail)
                created += 1
    
    db.session.commit()
    return created, updated


def seed_predefined_permissions():
    """
    Seed all predefined permissions and categories.
    
    Idempotent: Safe to run multiple times.
    - Creates permission categories
    - Creates permissions if not exist
    - Updates existing permissions
    - Creates permission details
    
    Returns:
        dict: Seeding results
    """
    print("\n" + "="*60)
    print("SEEDING PREDEFINED PERMISSIONS")
    print("="*60)
    
    # Seed categories
    print("\nSeeding permission categories...")
    cat_created, cat_updated = seed_permission_categories()
    print(f"  [+] Created: {cat_created} categories")
    print(f"  [*] Updated: {cat_updated} categories")
    
    # Seed permissions
    print("\nSeeding permissions...")
    perm_created, perm_updated = seed_permissions()
    print(f"  [+] Created: {perm_created} permissions")
    print(f"  [*] Updated: {perm_updated} permissions")
    
    # Seed permission details
    print("\nSeeding permission details...")
    detail_created, detail_updated = seed_permission_details()
    print(f"  [+] Created: {detail_created} details")
    print(f"  [*] Updated: {detail_updated} details")
    
    print("\n" + "="*60)
    print(f"Total: {cat_created + perm_created + detail_created} created")
    print(f"Total: {cat_updated + perm_updated + detail_updated} updated")
    print("="*60 + "\n")
    
    return {
        'categories_created': cat_created,
        'categories_updated': cat_updated,
        'permissions_created': perm_created,
        'permissions_updated': perm_updated,
        'details_created': detail_created,
        'details_updated': detail_updated,
    }


if __name__ == '__main__':
    # Run as standalone script for testing
    from app import create_app
    
    app = create_app()
    with app.app_context():
        seed_predefined_permissions()
