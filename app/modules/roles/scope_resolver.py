from app.modules.roles.repository import RolesRepository


class ScopeResolver:
    """Resolves role/class scope access and assigns scopes."""

    def __init__(self):
        self.repo = RolesRepository()

    def resolve_scope(self, role_id, scope_context):
        scopes = self.repo.get_role_scopes(role_id)
        matching = [scope for scope in scopes if scope.scope_type.name == scope_context]
        return matching

    def assign_scope(self, role_id, scope_type_id, scope_ids):
        from app.modules.roles.models import RoleScope

        RoleScope.query.filter_by(role_id=role_id, scope_type_id=scope_type_id).delete()
        self.repo.create_role_scope(role_id, scope_type_id)
        return True
