"""
Deployment Validators

Request validation for deployment creation and approval operations.
"""


class DeploymentValidator:
    """Validates deployment data and rules"""

    @staticmethod
    def validate_deployment_payload(payload):
        """Validate deployment creation payload"""
        errors = []

        if not payload.get('vehicle_id'):
            errors.append('Vehicle ID is required')

        if not payload.get('project_id'):
            errors.append('Project ID is required')

        if not payload.get('subzone_id'):
            errors.append('Subzone ID is required')

        deployment_type = payload.get('deployment_type', '').strip()
        if not deployment_type:
            errors.append('Deployment type is required')
        elif deployment_type not in ['Standard', 'Express', 'Special', 'Emergency']:
            errors.append(f'Invalid deployment type: {deployment_type}')

        return len(errors) == 0, errors

    @staticmethod
    def validate_approval_payload(payload):
        """Validate approval payload"""
        errors = []

        action = payload.get('approval_action', '').strip()
        if not action:
            errors.append('Approval action is required')
        elif action not in ['approve', 'reject', 'escalate']:
            errors.append(f'Invalid action: {action}')

        if action in ['reject', 'escalate']:
            reason = payload.get('reason', '').strip()
            if not reason:
                errors.append(f'Reason is required for {action}')

        return len(errors) == 0, errors
