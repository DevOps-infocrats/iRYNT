from app.modules.roles.repository import RolesRepository


class WorkflowAccessService:
    """Helper for workflow authority evaluation."""

    def __init__(self):
        self.repo = RolesRepository()

    def has_workflow_access(self, role_id, workflow_type, action):
        permissions = self.repo.get_role_workflow_permissions(role_id)
        workflow = next((w for w in permissions if w.workflow_type == workflow_type), None)
        if not workflow:
            return False

        action_map = {
            'approve': workflow.can_approve,
            'reject': workflow.can_reject,
            'escalate': workflow.can_escalate,
            'override': workflow.can_override,
            'close': workflow.can_close_workflow,
        }
        return action_map.get(action, False)

    def set_workflow_permissions(self, role_id, workflow_type, permissions):
        return self.repo.set_workflow_permission(role_id, workflow_type, permissions)
