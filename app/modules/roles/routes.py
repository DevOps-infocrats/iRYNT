from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user

from app.domain.auth.access import AccessManager
from app.modules.roles.services import RolesService
from app.modules.roles.repository import RolesRepository

roles_bp = Blueprint('roles', __name__, url_prefix='/roles', template_folder='templates')

role_service = RolesService()
role_repo = RolesRepository()


@roles_bp.before_request
@login_required
def check_access():
    """Check if user has access to roles module"""
    if not current_user or not AccessManager(current_user).has_permission('roles.view'):
        return jsonify({'error': 'Unauthorized'}), 403


@roles_bp.route('/', methods=['GET'])
def index():
    """Roles & Access Control dashboard"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    filters = {
        'search': request.args.get('search', ''),
        'is_system': request.args.get('is_system', None),
    }
    
    kpis = role_service.get_dashboard_kpis()
    roles_data = role_service.list_roles(filters, page, per_page)
    hierarchy = role_service.get_hierarchy_visualization()
    
    return render_template(
        'roles/list.html',
        kpis=kpis,
        roles=roles_data['roles'],
        total=roles_data['total'],
        page=roles_data['page'],
        per_page=roles_data['per_page'],
        pages=roles_data['pages'],
        hierarchy=hierarchy,
        filters=filters,
    )


@roles_bp.route('/<role_id>/detail', methods=['GET'])
def detail(role_id):
    """Get role details"""
    role_detail = role_service.get_role_detail(role_id)
    
    if not role_detail:
        return jsonify({'error': 'Role not found'}), 404
    
    permission_matrix = role_service.get_permission_matrix(role_id)
    
    return render_template(
        'roles/detail.html',
        role=role_detail,
        permission_matrix=permission_matrix,
    )


@roles_bp.route('/<role_id>/permissions', methods=['GET'])
def get_permissions(role_id):
    """Get role permissions (AJAX)"""
    permissions = role_repo.get_role_permissions(role_id)
    return jsonify({
        'permissions': [{'id': p.id, 'name': p.name} for p in permissions]
    })


@roles_bp.route('/<role_id>/matrix', methods=['GET'])
def get_matrix(role_id):
    """Get role permission matrix (AJAX)"""
    matrix = role_service.get_permission_matrix(role_id)
    return jsonify(matrix)


@roles_bp.route('/compare', methods=['GET'])
def compare():
    """Compare two roles"""
    role_id_1 = request.args.get('role1')
    role_id_2 = request.args.get('role2')
    
    if not role_id_1 or not role_id_2:
        return jsonify({'error': 'Missing role IDs'}), 400
    
    comparison = role_service.compare_roles(role_id_1, role_id_2)
    
    if not comparison:
        return jsonify({'error': 'Roles not found'}), 404
    
    return render_template(
        'roles/compare.html',
        comparison=comparison,
    )


@roles_bp.route('/hierarchy', methods=['GET'])
def get_hierarchy():
    """Get role hierarchy (AJAX)"""
    hierarchy = role_service.get_hierarchy_visualization()
    return jsonify(hierarchy)


@roles_bp.route('/kpis', methods=['GET'])
def get_kpis():
    """Get dashboard KPIs (AJAX)"""
    kpis = role_service.get_dashboard_kpis()
    return jsonify(kpis)


@roles_bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create new role"""
    permission_groups = role_repo.get_permission_groups()
    scope_types = role_repo.get_scope_types()

    if request.method == 'GET':
        return render_template(
            'roles/create.html',
            permission_groups=permission_groups,
            scope_types=scope_types,
        )

    # Handle form-based role creation from UI
    name = request.form.get('name')
    description = request.form.get('description')
    is_system = request.form.get('is_system') in ['1', 'true', 'True', 'on']
    scope_type_id = request.form.get('scope_type')
    permission_group_id = request.form.get('permission_group')

    if not name:
        return jsonify({'error': 'Role name is required'}), 400

    role = role_repo.create_role(name=name, description=description, is_system=is_system)

    if scope_type_id:
        role_repo.create_role_scope(role.id, scope_type_id, None)

    if permission_group_id:
        group_permissions = role_repo.get_permissions_by_group(permission_group_id)
        for permission in group_permissions:
            role_repo.add_permission_to_role(role.id, permission.id)

    return render_template('roles/detail.html', role=role_service.get_role_detail(role.id), permission_matrix=role_service.get_permission_matrix(role.id))


@roles_bp.route('/audit-logs', methods=['GET'])
def audit_logs():
    """Get audit logs for roles"""
    role_id = request.args.get('role_id')
    limit = request.args.get('limit', 50, type=int)
    
    logs = role_repo.get_role_audit_logs(role_id, limit)
    
    return jsonify({
        'logs': [
            {
                'action': log.action,
                'entity_type': log.entity_type,
                'timestamp': log.created_at.isoformat() if log.created_at else None,
                'user_id': log.changed_by_user_id,
            }
            for log in logs
        ]
    })

