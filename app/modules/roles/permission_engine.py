from app.domain.auth.access import AccessManager


class RolePermissionEngine:
    """Facade for role-level permission evaluation."""

    def __init__(self, user=None):
        self.user = user
        self.access_manager = AccessManager(user) if user else None

    def has_permission(self, permission_code: str) -> bool:
        if not self.access_manager:
            return False
        return self.access_manager.has_permission(permission_code)

    def requires_permission(self, permission_code: str):
        def decorator(func):
            def wrapper(*args, **kwargs):
                if not self.has_permission(permission_code):
                    return {'error': 'Unauthorized'}, 403
                return func(*args, **kwargs)
            return wrapper
        return decorator
