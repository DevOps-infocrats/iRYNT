"""
Idempotent Role Seeding System

This module seeds predefined roles from templates.
- Safe for multiple runs
- Updates existing roles with template definitions
- Preserves existing user assignments
- Normalizes role hierarchy
"""

from app.extensions import db
from app.modules.auth.models import Role
from app.modules.roles.template_services.role_template_service import RoleTemplateService, RoleTemplateManager


def seed_predefined_roles():
    """
    Seed all predefined roles from templates.
    
    Idempotent: Safe to run multiple times.
    - Creates new roles from templates
    - Updates existing roles to match templates
    - Preserves user-role assignments
    
    Returns:
        dict: Seeding results (created, updated, failed, skipped)
    """
    print("\n" + "="*60)
    print("SEEDING PREDEFINED ROLES FROM TEMPLATES")
    print("="*60)
    
    results = RoleTemplateManager.seed_predefined_roles()
    
    print(f"\n[+] Created: {len(results['created'])} roles")
    for role in results['created']:
        print(f"  - {role}")
    
    print(f"\n[*] Updated: {len(results['updated'])} roles")
    for role in results['updated']:
        print(f"  - {role}")
    
    if results['skipped']:
        print(f"\n[-] Skipped: {len(results['skipped'])} templates")
        for template in results['skipped']:
            print(f"  - {template}")
    
    if results['failed']:
        print(f"\n[!] Failed: {len(results['failed'])} operations")
        for failure in results['failed']:
            print(f"  - {failure}")
    
    print("\n" + "="*60)
    print(f"Role hierarchy established: 13 predefined roles")
    print("="*60 + "\n")
    
    return results


def ensure_predefined_roles():
    """
    Ensure all predefined roles exist in the database.
    
    Called during application initialization to guarantee
    the role hierarchy is properly seeded.
    """
    # Check if any predefined role exists
    super_admin = Role.query.filter_by(name='Super Admin').first()
    
    if not super_admin:
        # Not seeded yet, run seeding
        seed_predefined_roles()
    else:
        # Predefined roles exist, update them to keep them synchronized with template definitions
        print("Predefined roles already exist. Ensuring templates are current...")
        seed_predefined_roles()


if __name__ == '__main__':
    # Run as standalone script for testing
    from app import create_app
    
    app = create_app()
    with app.app_context():
        seed_predefined_roles()
