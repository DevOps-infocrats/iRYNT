"""
Sidebar Access Service

Provides permission-aware sidebar menu rendering based on user roles and permissions.
Ensures sidebar menus are dynamically generated and respect access control.
"""

from typing import Any, Dict, List, Optional

from app.domain.auth.access import AccessManager


class SidebarAccessService:
    """Service for managing sidebar access based on permissions and roles"""

    @staticmethod
    def filter_sidebar_menu(menu_items: List[Dict[str, Any]], user: Any = None, claims: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Filter sidebar menu items based on user permissions and roles.
        
        Args:
            menu_items: List of menu item dictionaries
            user: User object (defaults to current_user)
            claims: JWT claims dictionary
        
        Returns:
            Filtered list of menu items visible to the user
        """
        if not menu_items:
            return []
        
        manager = AccessManager(user, claims)
        visible_items = []
        
        for item in menu_items:
            # Check if item has permission requirement
            if item.get('permission') and not manager.has_permission(item['permission']):
                continue
            
            # Check if item has role requirement
            if item.get('roles'):
                if not manager.has_role(item['roles']):
                    continue
            
            # Check if item has scope requirement
            if item.get('scope'):
                scope_params = item.get('scope_params', {})
                if not manager.has_scope(**scope_params):
                    continue
            
            # Filter children recursively
            if item.get('children'):
                item['children'] = SidebarAccessService.filter_sidebar_menu(
                    item['children'], user, claims
                )
                # Only include parent if it has visible children or no children requirement
                if item.get('children') or item.get('show_without_children', False):
                    visible_items.append(item)
            else:
                visible_items.append(item)
        
        return visible_items

    @staticmethod
    def get_accessible_sidebar_sections(user: Any = None, claims: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Get list of sidebar section keys accessible to user.
        
        Args:
            user: User object (defaults to current_user)
            claims: JWT claims dictionary
        
        Returns:
            List of accessible sidebar section keys
        """
        manager = AccessManager(user, claims)
        
        # Define section permission mapping
        section_permissions = {
            'dashboard': 'dashboard.view',
            'masters': 'masters.view',
            'user_management': 'users.view',
            'deployments': 'deployments.view',
            'operations': 'operations.view',
            'workflows': 'workflows.view',
            'analytics': 'reports.analytics',
            'reporting': 'reports.view',
            'settings': 'settings.view',
            'admin': 'system.settings',
        }
        
        accessible = []
        for section, permission in section_permissions.items():
            if manager.has_permission(permission):
                accessible.append(section)
        
        # For super admin, return all sections
        if manager.is_superadmin():
            return list(section_permissions.keys())
        
        return accessible

    @staticmethod
    def is_menu_item_visible(item: Dict[str, Any], user: Any = None, claims: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if a specific menu item is visible to user.
        
        Args:
            item: Menu item dictionary
            user: User object (defaults to current_user)
            claims: JWT claims dictionary
        
        Returns:
            True if item is visible, False otherwise
        """
        manager = AccessManager(user, claims)
        
        # Check permission
        if item.get('permission') and not manager.has_permission(item['permission']):
            return False
        
        # Check role
        if item.get('roles') and not manager.has_role(item['roles']):
            return False
        
        # Check scope
        if item.get('scope'):
            scope_params = item.get('scope_params', {})
            if not manager.has_scope(**scope_params):
                return False
        
        return True

    @staticmethod
    def enrich_menu_with_visibility(menu_items: List[Dict[str, Any]], user: Any = None, claims: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Add visibility information to menu items without filtering.
        
        Useful for frontend processing of menu items.
        
        Args:
            menu_items: List of menu item dictionaries
            user: User object (defaults to current_user)
            claims: JWT claims dictionary
        
        Returns:
            Menu items with 'is_visible' attribute added
        """
        enriched = []
        
        for item in menu_items:
            is_visible = SidebarAccessService.is_menu_item_visible(item, user, claims)
            item['is_visible'] = is_visible
            
            if item.get('children'):
                item['children'] = SidebarAccessService.enrich_menu_with_visibility(
                    item['children'], user, claims
                )
            
            enriched.append(item)
        
        return enriched
