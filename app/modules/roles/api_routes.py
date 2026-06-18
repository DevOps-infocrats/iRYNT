from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.domain.auth.access import AccessManager
from app.modules.roles.repository import RolesRepository
from app.modules.roles.validators import RoleValidator
from app.modules.roles.permission_engine import RolePermissionEngine
from app.modules.roles.scope_resolver import ScopeResolver
from app.modules.roles.workflow_access_service import WorkflowAccessService

roles_api_bp = Blueprint('roles_api', __name__, url_prefix='/api/v1/roles')

repository = RolesRepository()
permission_engine = RolePermissionEngine()
scope_resolver = ScopeResolver()
workflow_service = WorkflowAccessService()


def _ensure_authorized(permission_key):
    if not current_user or not AccessManager(current_user).has_permission(permission_key):
        return jsonify({'error': 'Unauthorized'}), 403
    return None


@roles_api_bp.before_request
@login_required
def authorize_api_request():
    unauthorized_resp = _ensure_authorized('roles.manage')
    if unauthorized_resp:
        return unauthorized_resp


@roles_api_bp.route('/', methods=['POST'])
def create_role():
    payload = request.get_json() or {}
    errors = RoleValidator.validate_create(payload)
    if errors:
        return jsonify({'errors': errors}), 400

    role = repository.create_role(
        name=payload['name'],
        description=payload.get('description'),
        is_system=payload.get('is_system', False),
    )

    if payload.get('permissions'):
        for permission_id in payload['permissions']:
            repository.add_permission_to_role(role.id, permission_id)

    if payload.get('module_access'):
        for module_name, access_values in payload['module_access'].items():
            repository.set_module_access(role.id, module_name, access_values)

    if payload.get('workflow_permissions'):
        for workflow_type, permission_values in payload['workflow_permissions'].items():
            repository.set_workflow_permission(role.id, workflow_type, permission_values)

    return jsonify({'success': True, 'role_id': role.id}), 201


@roles_api_bp.route('/<role_id>', methods=['GET'])
def get_role(role_id):
    role_detail = repository.get_role_by_id(role_id)
    if not role_detail:
        return jsonify({'error': 'Role not found'}), 404

    return jsonify({
        'id': role_detail.id,
        'name': role_detail.name,
        'description': role_detail.description,
        'is_system': role_detail.is_system,
        'permissions': [p.name for p in role_detail.permissions],
    })


@roles_api_bp.route('/<role_id>/permissions', methods=['POST'])
def set_role_permissions(role_id):
    payload = request.get_json() or {}
    permission_ids = payload.get('permission_ids', [])
    if not isinstance(permission_ids, list):
        return jsonify({'error': 'permission_ids must be a list'}), 400

    existing_role = repository.get_role_by_id(role_id)
    if not existing_role:
        return jsonify({'error': 'Role not found'}), 404

    repository.update_role(role_id, permissions=[])
    for permission_id in permission_ids:
        repository.add_permission_to_role(role_id, permission_id)

    return jsonify({'success': True})


@roles_api_bp.route('/<role_id>/scope', methods=['POST'])
def set_role_scope(role_id):
    payload = request.get_json() or {}
    scope_type_id = payload.get('scope_type_id')
    scope_ids = payload.get('scope_ids', [])

    if not scope_type_id or not isinstance(scope_ids, list):
        return jsonify({'error': 'Invalid scope payload'}), 400

    if not repository.get_role_by_id(role_id):
        return jsonify({'error': 'Role not found'}), 404

    scope_resolver.assign_scope(role_id, scope_type_id, scope_ids)
    return jsonify({'success': True})


@roles_api_bp.route('/<role_id>/workflow', methods=['POST'])
def set_workflow_permissions(role_id):
    payload = request.get_json() or {}
    workflow_permissions = payload.get('workflow_permissions', {})

    if not isinstance(workflow_permissions, dict):
        return jsonify({'error': 'workflow_permissions must be a dictionary'}), 400

    if not repository.get_role_by_id(role_id):
        return jsonify({'error': 'Role not found'}), 404

    for workflow_type, permissions in workflow_permissions.items():
        workflow_service.set_workflow_permissions(role_id, workflow_type, permissions)

    return jsonify({'success': True})


@roles_api_bp.route('/permission-groups', methods=['GET'])
def permission_groups():
    groups = repository.get_permission_groups()
    return jsonify([
        {'id': group.id, 'name': group.name, 'category': group.category}
        for group in groups
    ])


@roles_api_bp.route('/scope-types', methods=['GET'])
def scope_types():
    types = repository.get_scope_types()
    return jsonify([
        {'id': scope.id, 'name': scope.name, 'description': scope.description}
        for scope in types
    ])
