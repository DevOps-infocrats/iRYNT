"""
Role Template Service

Manages predefined role templates and applies them to roles in the system.
Supports loading templates, applying to roles, and managing role lifecycles.
"""

import json
import os
from typing import Dict, List, Optional, Any

from app.modules.auth.models import Permission, Role
from app.extensions import db


class RoleTemplateService:
    """Service to manage predefined role templates"""

    TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')

    @staticmethod
    def get_template_path(role_key: str) -> str:
        """Get the path to a role template file"""
        filename = f"{role_key.lower().replace(' ', '_')}.json"
        return os.path.join(RoleTemplateService.TEMPLATE_DIR, filename)

    @staticmethod
    def load_template(role_key: str) -> Optional[Dict[str, Any]]:
        """Load a role template from JSON file"""
        template_path = RoleTemplateService.get_template_path(role_key)
        
        if not os.path.exists(template_path):
            return None
        
        try:
            with open(template_path, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to load role template {role_key}: {str(e)}")

    @staticmethod
    def list_templates() -> List[str]:
        """List all available role templates"""
        templates = []
        if os.path.exists(RoleTemplateService.TEMPLATE_DIR):
            for filename in os.listdir(RoleTemplateService.TEMPLATE_DIR):
                if filename.endswith('.json'):
                    role_key = filename[:-5]  # Remove .json extension
                    templates.append(role_key)
        return sorted(templates)

    @staticmethod
    def apply_template_to_role(role: Role, template: Dict[str, Any]) -> None:
        """Apply template permissions and attributes to a role"""
        # Update role attributes from template
        if 'description' in template:
            role.description = template['description']
        
        if 'is_system' in template:
            role.is_system = template['is_system']
        
        # Clear existing permissions
        role.permissions.clear()
        
        # Add permissions from template
        if 'permissions' in template:
            for permission_name in template['permissions']:
                permission = Permission.query.filter_by(name=permission_name).first()
                if permission:
                    role.permissions.append(permission)
                else:
                    # Log missing permission but don't fail
                    print(f"Warning: Permission '{permission_name}' not found for role '{role.name}'")
        
        db.session.commit()

    @staticmethod
    def apply_template_by_name(role_name: str, template_key: str) -> Optional[Role]:
        """Apply a template to an existing role by name"""
        role = Role.query.filter_by(name=role_name).first()
        
        if not role:
            return None
        
        template = RoleTemplateService.load_template(template_key)
        
        if not template:
            return None
        
        RoleTemplateService.apply_template_to_role(role, template)
        return role

    @staticmethod
    def create_role_from_template(template_key: str) -> Optional[Role]:
        """Create a new role from a template"""
        template = RoleTemplateService.load_template(template_key)
        
        if not template:
            return None
        
        # Check if role already exists
        role_name = template.get('role_name')
        existing_role = Role.query.filter_by(name=role_name).first()
        
        if existing_role:
            # Apply template to existing role
            RoleTemplateService.apply_template_to_role(existing_role, template)
            return existing_role
        
        # Create new role
        role = Role(
            name=role_name,
            description=template.get('description', ''),
            is_system=template.get('is_system', False)
        )
        
        db.session.add(role)
        db.session.flush()  # Get the ID before adding permissions
        
        # Apply template
        RoleTemplateService.apply_template_to_role(role, template)
        
        return role

    @staticmethod
    def get_template_metadata(template_key: str) -> Optional[Dict[str, Any]]:
        """Get template metadata (role name, level, tier, description)"""
        template = RoleTemplateService.load_template(template_key)
        
        if not template:
            return None
        
        return {
            'template_key': template_key,
            'role_name': template.get('role_name'),
            'level': template.get('level'),
            'tier': template.get('tier'),
            'description': template.get('description'),
            'scope': template.get('scope'),
            'permissions_count': len(template.get('permissions', [])),
            'sidebar_sections': len(template.get('sidebar_access', [])),
            'is_predefined': template.get('is_predefined', True),
            'is_system': template.get('is_system', False),
        }

    @staticmethod
    def get_all_templates_metadata() -> List[Dict[str, Any]]:
        """Get metadata for all available templates"""
        templates = []
        
        for template_key in RoleTemplateService.list_templates():
            metadata = RoleTemplateService.get_template_metadata(template_key)
            if metadata:
                templates.append(metadata)
        
        # Sort by level descending
        return sorted(templates, key=lambda x: x.get('level', 0), reverse=True)

    @staticmethod
    def validate_template(template_key: str) -> tuple[bool, List[str]]:
        """Validate a role template for completeness and correctness"""
        template = RoleTemplateService.load_template(template_key)
        
        if not template:
            return False, [f"Template '{template_key}' not found"]
        
        errors = []
        
        # Check required fields
        required_fields = ['role_name', 'level', 'tier', 'description', 'permissions', 'workflow_rights', 'sidebar_access']
        for field in required_fields:
            if field not in template:
                errors.append(f"Missing required field: {field}")
        
        # Check level is 1-13
        level = template.get('level')
        if not isinstance(level, int) or level < 1 or level > 13:
            errors.append(f"Invalid level: {level} (must be 1-13)")
        
        # Check tier is valid
        valid_tiers = ['system', 'corporate', 'circle', 'field']
        if template.get('tier') not in valid_tiers:
            errors.append(f"Invalid tier: {template.get('tier')} (must be one of {valid_tiers})")
        
        # Check scope is valid
        valid_scopes = ['global', 'company', 'circle', 'operational']
        if template.get('scope') not in valid_scopes:
            errors.append(f"Invalid scope: {template.get('scope')} (must be one of {valid_scopes})")
        
        # Check workflow_rights structure
        workflow_rights = template.get('workflow_rights', {})
        required_workflow_fields = ['can_approve', 'can_reject', 'can_escalate', 'can_override', 'approval_level']
        for field in required_workflow_fields:
            if field not in workflow_rights:
                errors.append(f"Missing workflow_right field: {field}")
        
        return len(errors) == 0, errors


class RoleTemplateManager:
    """Manager for role template operations"""

    @staticmethod
    def seed_predefined_roles() -> Dict[str, Any]:
        """Seed all predefined roles from templates (idempotent)"""
        results = {
            'created': [],
            'updated': [],
            'failed': [],
            'skipped': [],
        }
        
        for template_key in RoleTemplateService.list_templates():
            try:
                template = RoleTemplateService.load_template(template_key)
                if not template:
                    results['skipped'].append(template_key)
                    continue
                
                role_name = template.get('role_name')
                existing_role = Role.query.filter_by(name=role_name).first()
                
                if existing_role:
                    # Apply template to existing role
                    RoleTemplateService.apply_template_to_role(existing_role, template)
                    results['updated'].append(role_name)
                else:
                    # Create new role from template
                    role = RoleTemplateService.create_role_from_template(template_key)
                    if role:
                        results['created'].append(role_name)
                    else:
                        results['failed'].append(template_key)
                
            except Exception as e:
                results['failed'].append(f"{template_key}: {str(e)}")
        
        return results

    @staticmethod
    def get_role_permissions_by_template(template_key: str) -> List[str]:
        """Get the list of permissions for a role template"""
        template = RoleTemplateService.load_template(template_key)
        
        if not template:
            return []
        
        return template.get('permissions', [])

    @staticmethod
    def get_role_workflow_rights(template_key: str) -> Dict[str, Any]:
        """Get workflow rights for a role template"""
        template = RoleTemplateService.load_template(template_key)
        
        if not template:
            return {}
        
        return template.get('workflow_rights', {})

    @staticmethod
    def get_role_sidebar_access(template_key: str) -> List[str]:
        """Get sidebar access sections for a role template"""
        template = RoleTemplateService.load_template(template_key)
        
        if not template:
            return []
        
        return template.get('sidebar_access', [])
