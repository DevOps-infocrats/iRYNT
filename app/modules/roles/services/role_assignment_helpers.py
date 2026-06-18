"""
Role Assignment Helpers

Provides convenient helpers for assigning roles to users and managing
role lifecycle operations safely.
"""

from typing import List, Optional

from app.extensions import db
from app.modules.auth.models import Role, User
from app.modules.roles.services.role_template_service import RoleTemplateService


def assign_role_to_user(user: User, role_name: str, as_primary: bool = True) -> bool:
    """
    Assign a role to a user.
    
    Args:
        user: User object
        role_name: Name of the role to assign
        as_primary: If True, set as primary role; if False, add to roles list
    
    Returns:
        True if successful, False if role not found
    """
    role = Role.query.filter_by(name=role_name).first()
    
    if not role:
        return False
    
    if as_primary:
        user.primary_role = role
    
    # Also add to roles list if not already present
    if role not in user.roles:
        user.roles.append(role)
    
    db.session.commit()
    return True


def assign_predefined_role_to_user(user: User, role_level: int) -> bool:
    """
    Assign a predefined role by level (1-13) to a user.
    
    Args:
        user: User object
        role_level: Role level (1-13)
    
    Returns:
        True if successful, False if role not found
    """
    # Map level to role name
    level_to_role = {
        13: 'Super Admin',
        12: 'Corporate Admin',
        11: 'Director',
        10: 'Key Account Manager',
        9: 'PMO',
        8: 'Corporate Customer',
        7: 'Circle Admin',
        6: 'CBH',
        5: 'Circle KAM',
        4: 'MIS',
        3: 'Circle Customer',
        2: 'Driver',
        1: 'Helper',
    }
    
    role_name = level_to_role.get(role_level)
    if not role_name:
        return False
    
    return assign_role_to_user(user, role_name)


def get_user_role_level(user: User) -> int:
    """
    Get the access level of a user based on their role.
    
    Returns:
        Role level (0 if no role)
    """
    if not user or not user.primary_role:
        return 0
    
    # Get level from ROLE_HIERARCHY or from RoleHierarchy model
    from app.domain.auth.access import ROLE_HIERARCHY
    
    role_name = user.primary_role.name.lower()
    return ROLE_HIERARCHY.get(role_name, 0)


def can_manage_user(manager_user: User, target_user: User) -> bool:
    """
    Check if manager_user can manage target_user based on role levels.
    
    Generally, a user can manage users with equal or lower role levels.
    
    Args:
        manager_user: User attempting to manage
        target_user: User being managed
    
    Returns:
        True if manager can manage target, False otherwise
    """
    manager_level = get_user_role_level(manager_user)
    target_level = get_user_role_level(target_user)
    
    # Can only manage users with equal or lower level
    return manager_level >= target_level


def get_available_roles_for_assignment(assigner: User) -> List[Role]:
    """
    Get list of roles that an assigner can assign to other users.
    
    Generally, users can assign roles with equal or lower levels.
    
    Args:
        assigner: User doing the assignment
    
    Returns:
        List of assignable roles
    """
    assigner_level = get_user_role_level(assigner)
    
    # Get all roles and filter by assignable levels
    from app.modules.roles.models import RoleHierarchy
    
    assignable_role_ids = (
        db.session.query(RoleHierarchy.role_id)
        .filter(RoleHierarchy.level <= assigner_level)
        .all()
    )
    
    assignable_ids = [r[0] for r in assignable_role_ids]
    
    if assignable_ids:
        return Role.query.filter(Role.id.in_(assignable_ids)).all()
    
    return []


def assign_template_permissions_to_role(role_name: str) -> bool:
    """
    Apply template permissions to an existing role.
    
    Useful for syncing a role with its template definition.
    
    Args:
        role_name: Name of the role
    
    Returns:
        True if successful, False if role not found
    """
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return False
    
    # Find matching template
    for template_key in RoleTemplateService.list_templates():
        template = RoleTemplateService.load_template(template_key)
        if template and template.get('role_name') == role_name:
            RoleTemplateService.apply_template_to_role(role, template)
            return True
    
    return False


def remove_role_from_user(user: User, role_name: str) -> bool:
    """
    Remove a role from a user.
    
    Args:
        user: User object
        role_name: Name of the role to remove
    
    Returns:
        True if successful, False if role not found
    """
    role = Role.query.filter_by(name=role_name).first()
    
    if not role:
        return False
    
    # Remove from primary role if applicable
    if user.primary_role and user.primary_role.id == role.id:
        user.primary_role = None
    
    # Remove from roles list
    if role in user.roles:
        user.roles.remove(role)
    
    db.session.commit()
    return True


def transfer_user_to_role(user: User, new_role_name: str) -> bool:
    """
    Transfer a user to a new role, removing previous roles.
    
    Args:
        user: User object
        new_role_name: Name of the new role
    
    Returns:
        True if successful, False if new role not found
    """
    new_role = Role.query.filter_by(name=new_role_name).first()
    
    if not new_role:
        return False
    
    # Clear existing roles
    user.primary_role = None
    user.roles.clear()
    
    # Assign new role
    user.primary_role = new_role
    user.roles.append(new_role)
    
    db.session.commit()
    return True
