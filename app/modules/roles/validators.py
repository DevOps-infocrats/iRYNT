from typing import Dict, List


class RoleValidator:
    """Validation helpers for role payloads."""

    @staticmethod
    def validate_create(payload: Dict) -> List[str]:
        errors = []

        if not payload.get('name'):
            errors.append('Role name is required.')
        if payload.get('is_system') not in [None, True, False, 0, 1, '0', '1', 'true', 'false']:
            errors.append('System role flag must be boolean or equivalent.')

        if payload.get('permissions') is not None and not isinstance(payload['permissions'], list):
            errors.append('Permissions must be a list of permission IDs.')

        if payload.get('module_access') is not None and not isinstance(payload['module_access'], dict):
            errors.append('Module access must be a dictionary.')

        return errors
