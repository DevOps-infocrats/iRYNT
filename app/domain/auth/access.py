from typing import Any, Dict, Iterable, List, Optional

from flask_jwt_extended import get_jwt, verify_jwt_in_request
from flask_login import current_user


ROLE_HIERARCHY = {
    'super admin': 13,
    'corporate admin': 12,
    'director': 11,
    'key account manager': 10,
    'kam': 10,
    'pmo': 9,
    'corporate customer': 8,
    'circle level admin': 7,
    'cbh': 6,
    'mis': 4,
    'circle customer': 3,
    'driver': 2,
    'helper': 1,
}

WORKFLOW_RIGHTS_BY_ROLE = {
    'super admin': {'can_approve', 'can_reject', 'can_escalate', 'can_override'},
    'corporate admin': {'can_approve', 'can_reject', 'can_escalate'},
    'director': {'can_approve', 'can_reject', 'can_escalate'},
    'key account manager': {'can_approve', 'can_reject'},
    'pmo': {'can_approve'},
    'circle level admin': {'can_approve', 'can_reject'},
    'cbh': {'can_approve'},
}

SCOPE_FIELDS = ('company_id', 'circle_id', 'client_id', 'project_id', 'subzone_id')


def _claims() -> Dict[str, Any]:
    try:
        verify_jwt_in_request(optional=True)
        return get_jwt()
    except Exception:
        return {}


class PermissionEngine:
    @staticmethod
    def normalize(permission_name: Optional[str]) -> Optional[str]:
        if permission_name is None:
            return None
        return permission_name.strip().lower()

    @staticmethod
    def parse(permission_name: Optional[str]) -> Dict[str, Optional[str]]:
        normalized = PermissionEngine.normalize(permission_name)
        if not normalized:
            return {'module': None, 'action': None, 'code': None}
        parts = normalized.split('.')
        if len(parts) == 1:
            return {'module': None, 'action': parts[0], 'code': normalized}
        return {
            'module': parts[0],
            'action': '.'.join(parts[1:]),
            'code': normalized,
        }


class ScopeResolver:
    def __init__(self, user: Any = None, claims: Optional[Dict[str, Any]] = None):
        self.user = user or current_user
        self.claims = claims if claims is not None else _claims()

    def get_scope(self) -> Dict[str, Any]:
        if self.user and getattr(self.user, 'is_authenticated', False):
            return {field: getattr(self.user, field, None) for field in SCOPE_FIELDS}
        return {field: self.claims.get(field) for field in SCOPE_FIELDS}

    def has_scope(
        self,
        company_id: Optional[str] = None,
        circle_id: Optional[str] = None,
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        subzone_id: Optional[str] = None,
    ) -> bool:
        scope = self.get_scope()
        checks = {
            'company_id': company_id,
            'circle_id': circle_id,
            'client_id': client_id,
            'project_id': project_id,
            'subzone_id': subzone_id,
        }
        for field, expected in checks.items():
            if expected is not None and scope.get(field) != expected:
                return False
        return True


class AccessManager:
    def __init__(self, user: Any = None, claims: Optional[Dict[str, Any]] = None):
        self.user = user or current_user
        self.claims = claims if claims is not None else _claims()
        self.scope_resolver = ScopeResolver(self.user, self.claims)

    def is_authenticated(self) -> bool:
        return bool(self.user and getattr(self.user, 'is_authenticated', False))

    def get_role_names(self) -> List[str]:
        if self.is_authenticated():
            names = []
            if getattr(self.user, 'primary_role', None):
                names.append(getattr(self.user.primary_role, 'name', '').lower())
            names.extend([getattr(role, 'name', '').lower() for role in getattr(self.user, 'roles', []) if getattr(role, 'name', None)])
            return [name for name in names if name]
        role_name = self.claims.get('role')
        if role_name:
            return [role_name.lower()]
        return []

    def get_role_level(self) -> int:
        levels = [ROLE_HIERARCHY.get(name, 0) for name in self.get_role_names()]
        return max(levels, default=0)

    def is_superadmin(self) -> bool:
        return 'super admin' in self.get_role_names()

    def has_role(self, roles: Any) -> bool:
        if roles is None:
            return True
        allowed = {role.lower() for role in roles} if isinstance(roles, (list, tuple, set)) else {str(roles).lower()}
        if self.is_superadmin():
            return True
        return bool(set(self.get_role_names()) & allowed)

    def get_permissions(self) -> List[str]:
        if self.is_authenticated():
            permissions = set()
            primary_role = getattr(self.user, 'primary_role', None)
            if primary_role is not None:
                permissions.update({perm.name.lower() for perm in getattr(primary_role, 'permissions', []) if getattr(perm, 'name', None)})
            for role in getattr(self.user, 'roles', []):
                permissions.update({perm.name.lower() for perm in getattr(role, 'permissions', []) if getattr(perm, 'name', None)})
            return sorted(permissions)
        permissions = self.claims.get('permissions', [])
        if isinstance(permissions, str):
            permissions = [permissions]
        return [perm.lower() for perm in permissions if isinstance(perm, str)]

    def has_permission(self, permission_name: Any) -> bool:
        normalized = PermissionEngine.normalize(permission_name)
        if normalized is None:
            return True
        if self.is_superadmin():
            return True
        return normalized in self.get_permissions()

    def has_scope(
        self,
        company_id: Optional[str] = None,
        circle_id: Optional[str] = None,
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        subzone_id: Optional[str] = None,
    ) -> bool:
        return self.scope_resolver.has_scope(company_id, circle_id, client_id, project_id, subzone_id)

    def has_workflow_right(self, right_name: str, module: Optional[str] = None) -> bool:
        if self.is_superadmin():
            return True
        right_name = str(right_name).lower().strip()
        role_names = self.get_role_names()
        for role in role_names:
            if right_name in WORKFLOW_RIGHTS_BY_ROLE.get(role, set()):
                return True
        if module:
            permission_code = f'{module}.{right_name}'
            if self.has_permission(permission_code):
                return True
        return False


def access_manager(user: Any = None, claims: Optional[Dict[str, Any]] = None) -> AccessManager:
    return AccessManager(user, claims)
