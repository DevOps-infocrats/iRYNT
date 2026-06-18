from app.modules.roles.repository import RolesRepository


class InheritanceService:
    """Computes effective permissions and scope inheritance across role tiers."""

    def __init__(self):
        self.repo = RolesRepository()

    def get_effective_permissions(self, role_id):
        hierarchy = self.repo.get_role_hierarchy(role_id)
        if not hierarchy:
            return self.repo.get_role_permissions(role_id)

        parent_permissions = []
        if hierarchy.parent_level is not None:
            parent_role = self.repo.get_hierarchy_by_level(hierarchy.parent_level)
            if parent_role:
                parent_permissions = self.repo.get_role_permissions(parent_role.role_id)

        current_permissions = self.repo.get_role_permissions(role_id)
        combined = {perm.id: perm for perm in parent_permissions + current_permissions}
        return list(combined.values())

    def get_effective_scope(self, role_id):
        scopes = self.repo.get_role_scopes(role_id)
        return scopes
