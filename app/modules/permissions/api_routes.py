"""
Permission Management API Routes

RESTful API endpoints for permission management
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.core.decorators import permission_required
from app.modules.permissions.services import PermissionService
from app.modules.permissions.validators import PermissionValidator
from app.modules.permissions.schemas import (
    PermissionListSchema,
    PermissionCreateSchema,
    PermissionUpdateSchema,
    RolePermissionsSchema,
)
from app.modules.auth.models import Permission, Role

permissions_api_bp = Blueprint('permissions_api', __name__, url_prefix='/api/v1/permissions')
service = PermissionService()


# Permission endpoints

@permissions_api_bp.route('', methods=['GET'])
@login_required
@permission_required('permissions.view')
def list_permissions():
    """Get all permissions with pagination"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    search = request.args.get('search', '', type=str)
    module_filter = request.args.get('module', '', type=str)

    skip = (page - 1) * limit

    if search:
        permissions, total = service.search_permissions(search, skip, limit)
    else:
        filters = {}
        if module_filter:
            filters['module'] = module_filter
        if filters:
            permissions, total = service.filter_permissions(filters, skip, limit)
        else:
            permissions, total = service.repository.get_all_permissions(skip=skip, limit=limit)

    schema = PermissionListSchema(many=True)
    result = schema.dump(permissions)

    return jsonify({
        'success': True,
        'data': result,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total,
            'total_pages': (total + limit - 1) // limit,
        }
    }), 200


@permissions_api_bp.route('/<permission_id>', methods=['GET'])
@login_required
@permission_required('permissions.view')
def get_permission(permission_id):
    """Get a specific permission"""
    permission = service.repository.get_permission_by_id(permission_id)
    if not permission:
        return jsonify({'success': False, 'error': 'Permission not found'}), 404

    detail = service.repository.get_permission_detail(permission_id)
    workflow_access = service.repository.get_permission_workflow_access(permission_id)

    return jsonify({
        'success': True,
        'data': {
            'id': permission.id,
            'name': permission.name,
            'description': permission.description,
            'detail': {
                'module': detail.module if detail else None,
                'action': detail.action if detail else None,
                'scope_type': detail.scope_type if detail else 'global',
                'security_level': detail.security_level if detail else 'medium',
                'is_active': detail.is_active if detail else True,
            },
            'workflow_access': {
                'workflow_type': workflow_access.workflow_type if workflow_access else None,
                'can_approve': workflow_access.can_approve if workflow_access else False,
                'can_reject': workflow_access.can_reject if workflow_access else False,
                'can_escalate': workflow_access.can_escalate if workflow_access else False,
                'can_override': workflow_access.can_override if workflow_access else False,
            } if workflow_access else None,
        }
    }), 200


@permissions_api_bp.route('', methods=['POST'])
@login_required
@permission_required('permissions.create')
def create_permission():
    """Create a new permission"""
    data = request.get_json()

    # Validate
    valid, errors = PermissionValidator.validate_permission_data(data)
    if not valid:
        return jsonify({'success': False, 'errors': errors}), 400

    valid, error = PermissionValidator.validate_permission_uniqueness(data['code'])
    if not valid:
        return jsonify({'success': False, 'errors': [error]}), 400

    # Create
    permission, error = service.create_permission(data)
    if error:
        return jsonify({'success': False, 'errors': [error]}), 400

    return jsonify({
        'success': True,
        'data': {
            'id': permission.id,
            'name': permission.name,
            'code': data['code'],
        },
        'message': 'Permission created successfully'
    }), 201


@permissions_api_bp.route('/<permission_id>', methods=['PUT'])
@login_required
@permission_required('permissions.edit')
def update_permission(permission_id):
    """Update a permission"""
    data = request.get_json()

    permission, error = service.update_permission(permission_id, data)
    if error:
        return jsonify({'success': False, 'errors': [error]}), 400

    return jsonify({
        'success': True,
        'data': {
            'id': permission.id,
            'name': permission.name,
        },
        'message': 'Permission updated successfully'
    }), 200


@permissions_api_bp.route('/<permission_id>', methods=['DELETE'])
@login_required
@permission_required('permissions.delete')
def delete_permission(permission_id):
    """Delete a permission"""
    success, error = service.delete_permission(permission_id)

    if not success:
        return jsonify({'success': False, 'errors': [error]}), 400

    return jsonify({
        'success': True,
        'message': 'Permission deleted successfully'
    }), 200


# Role-Permission endpoints

@permissions_api_bp.route('/roles/<role_id>/permissions', methods=['GET'])
@login_required
@permission_required('permissions.view')
def get_role_permissions(role_id):
    """Get permissions for a role"""
    role = Role.query.get(role_id)
    if not role:
        return jsonify({'success': False, 'error': 'Role not found'}), 404

    permissions_grouped = service.get_role_permissions_grouped(role_id)
    analytics = service.get_role_permission_analytics(role_id)

    return jsonify({
        'success': True,
        'data': {
            'role_id': role_id,
            'role_name': role.name,
            'permissions_count': len(role.permissions),
            'permissions': [p.name for p in role.permissions],
            'grouped': permissions_grouped,
            'analytics': analytics,
        }
    }), 200


@permissions_api_bp.route('/roles/<role_id>/assign', methods=['POST'])
@login_required
@permission_required('permissions.assign')
def assign_permission_to_role(role_id):
    """Assign a permission to a role"""
    data = request.get_json()
    permission_id = data.get('permission_id')

    # Validate
    valid, errors = PermissionValidator.validate_role_permission_assignment(role_id, permission_id)
    if not valid:
        return jsonify({'success': False, 'errors': errors}), 400

    # Assign
    success = service.assign_permission_to_role(role_id, permission_id)
    if not success:
        return jsonify({'success': False, 'errors': ['Failed to assign permission']}), 400

    return jsonify({
        'success': True,
        'message': 'Permission assigned successfully'
    }), 200


@permissions_api_bp.route('/roles/<role_id>/revoke', methods=['POST'])
@login_required
@permission_required('permissions.revoke')
def revoke_permission_from_role(role_id):
    """Revoke a permission from a role"""
    data = request.get_json()
    permission_id = data.get('permission_id')

    success = service.revoke_permission_from_role(role_id, permission_id)
    if not success:
        return jsonify({'success': False, 'errors': ['Failed to revoke permission']}), 400

    return jsonify({
        'success': True,
        'message': 'Permission revoked successfully'
    }), 200


@permissions_api_bp.route('/roles/<role_id>/bulk-assign', methods=['POST'])
@login_required
@permission_required('permissions.assign')
def bulk_assign_permissions(role_id):
    """Bulk assign permissions to a role"""
    data = request.get_json()
    permission_ids = data.get('permission_ids', [])

    if not isinstance(permission_ids, list):
        return jsonify({'success': False, 'errors': ['permission_ids must be a list']}), 400

    success, error = service.assign_permissions_bulk(role_id, permission_ids)
    if not success:
        return jsonify({'success': False, 'errors': [error]}), 400

    return jsonify({
        'success': True,
        'message': f'{len(permission_ids)} permissions assigned successfully'
    }), 200


# Matrix endpoint

@permissions_api_bp.route('/matrix', methods=['GET'])
@login_required
@permission_required('permissions.view')
def get_permission_matrix():
    """Get permission matrix"""
    module = request.args.get('module', type=str)
    role_id = request.args.get('role_id', type=str)

    matrix = service.get_permission_matrix(module=module, role_id=role_id)

    return jsonify({
        'success': True,
        'data': matrix
    }), 200


# Analytics endpoints

@permissions_api_bp.route('/analytics', methods=['GET'])
@login_required
@permission_required('permissions.view')
def get_analytics():
    """Get permission analytics"""
    analytics_data = service.get_permission_analytics()

    return jsonify({
        'success': True,
        'data': analytics_data
    }), 200


@permissions_api_bp.route('/analytics/role/<role_id>', methods=['GET'])
@login_required
@permission_required('permissions.view')
def get_role_analytics(role_id):
    """Get analytics for a specific role"""
    analytics_data = service.get_role_permission_analytics(role_id)

    return jsonify({
        'success': True,
        'data': analytics_data
    }), 200


# Audit endpoints

@permissions_api_bp.route('/audit', methods=['GET'])
@login_required
@permission_required('permissions.view_audit')
def get_audit_logs():
    """Get audit logs"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    role_id = request.args.get('role_id', type=str)
    permission_id = request.args.get('permission_id', type=str)

    skip = (page - 1) * limit
    audit_logs, total = service.repository.get_audit_logs(
        skip=skip,
        limit=limit,
        role_id=role_id,
        permission_id=permission_id
    )

    return jsonify({
        'success': True,
        'data': [{
            'id': log.id,
            'action': log.action,
            'entity_type': log.entity_type,
            'status': log.status,
            'severity': log.severity,
            'created_at': log.created_at.isoformat(),
        } for log in audit_logs],
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total,
            'total_pages': (total + limit - 1) // limit,
        }
    }), 200


# Dashboard endpoint

@permissions_api_bp.route('/dashboard', methods=['GET'])
@login_required
@permission_required('permissions.view')
def get_dashboard_data():
    """Get dashboard KPIs"""
    kpis = service.get_dashboard_kpis()
    analytics = service.get_permission_analytics()

    return jsonify({
        'success': True,
        'data': {
            'kpis': kpis,
            'analytics': analytics,
        }
    }), 200


# Search endpoint

@permissions_api_bp.route('/search', methods=['GET'])
@login_required
@permission_required('permissions.view')
def search():
    """Search permissions"""
    query = request.args.get('q', '', type=str)
    limit = request.args.get('limit', 10, type=int)

    if not query:
        return jsonify({'success': True, 'data': []}), 200

    permissions, _ = service.search_permissions(query, limit=limit)

    return jsonify({
        'success': True,
        'data': [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
        } for p in permissions]
    }), 200
