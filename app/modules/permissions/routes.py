"""
Permission Management Web Routes

User interface routes for managing permissions
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app.modules.permissions.services import PermissionService
from app.modules.permissions.validators import PermissionValidator
from app.modules.auth.models import Role
from app.core.decorators import permission_required
from app.domain.auth.policies.auth_policy import has_permission

permissions_bp = Blueprint('permissions', __name__, url_prefix='/permissions')
service = PermissionService()


# Dashboard Routes

@permissions_bp.route('/', methods=['GET'])
@login_required
@permission_required('permissions.view')
def dashboard():
    """Permissions dashboard"""
    kpis = service.get_dashboard_kpis()
    categories = service.get_all_categories()
    
    return render_template(
        'permissions/dashboard.html',
        kpis=kpis,
        categories=categories,
        has_permission=has_permission
    )


# Permission Management Routes

@permissions_bp.route('/registry', methods=['GET'])
@login_required
@permission_required('permissions.view')
def permission_registry():
    """Permission registry/list view"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    search = request.args.get('search', '', type=str)
    module_filter = request.args.get('module', '', type=str)
    action_filter = request.args.get('action', '', type=str)
    security_filter = request.args.get('security_level', '', type=str)
    
    skip = (page - 1) * limit

    # Build filters
    filters = {}
    if module_filter:
        filters['module'] = module_filter
    if action_filter:
        filters['action'] = action_filter
    if security_filter:
        filters['security_level'] = security_filter

    if search:
        permissions, total = service.search_permissions(search, skip, limit)
    elif filters:
        permissions, total = service.filter_permissions(filters, skip, limit)
    else:
        permissions, total = service.repository.get_all_permissions(skip=skip, limit=limit)

    total_pages = (total + limit - 1) // limit

    return render_template(
        'permissions/registry.html',
        permissions=permissions,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        search=search,
        module_filter=module_filter,
        action_filter=action_filter,
        security_filter=security_filter,
        has_permission=has_permission
    )


@permissions_bp.route('/<permission_id>', methods=['GET'])
@login_required
@permission_required('permissions.view')
def permission_details(permission_id):
    """Permission details/intelligence panel"""
    permission = service.repository.get_permission_by_id(permission_id)
    if not permission:
        flash('Permission not found', 'danger')
        return redirect(url_for('permissions.permission_registry'))

    detail = service.repository.get_permission_detail(permission_id)
    workflow_access = service.repository.get_permission_workflow_access(permission_id)
    audit_logs, _ = service.repository.get_audit_logs(permission_id=permission_id, limit=20)

    # Get roles that have this permission
    assigned_roles = permission.roles if hasattr(permission, 'roles') else []

    return render_template(
        'permissions/details.html',
        permission=permission,
        detail=detail,
        workflow_access=workflow_access,
        assigned_roles=assigned_roles,
        audit_logs=audit_logs,
        has_permission=has_permission
    )


@permissions_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('permissions.create')
def create_permission():
    """Create new permission (multi-step wizard)"""
    categories = service.get_all_categories()

    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form.to_dict(flat=True)

        # Convert boolean form values
        for bool_field in ['is_active', 'can_delegate', 'requires_mfa']:
            if bool_field in request.form:
                data[bool_field] = request.form.get(bool_field) in ['on', 'true', '1', 'yes']

        # Validate data
        valid, errors = PermissionValidator.validate_permission_data(data)
        if not valid:
            if request.is_json:
                return jsonify({'success': False, 'errors': errors}), 400
            flash('Please correct the form errors.', 'danger')
            return render_template(
                'permissions/create.html',
                categories=categories,
                errors=errors,
                data=data,
                has_permission=has_permission
            )

        # Check uniqueness
        valid, error = PermissionValidator.validate_permission_uniqueness(data.get('code'))
        if not valid:
            if request.is_json:
                return jsonify({'success': False, 'errors': [error]}), 400
            flash(error, 'danger')
            return render_template(
                'permissions/create.html',
                categories=categories,
                errors=[error],
                data=data,
                has_permission=has_permission
            )

        # Create permission
        permission, error = service.create_permission(data)
        if error:
            if request.is_json:
                return jsonify({'success': False, 'errors': [error]}), 400
            flash(error, 'danger')
            return render_template(
                'permissions/create.html',
                categories=categories,
                errors=[error],
                data=data,
                has_permission=has_permission
            )

        if request.is_json:
            return jsonify({
                'success': True,
                'permission_id': permission.id,
                'message': 'Permission created successfully'
            }), 201

        flash('Permission created successfully.', 'success')
        return redirect(url_for('permissions.permission_details', permission_id=permission.id))

    return render_template(
        'permissions/create.html',
        categories=categories,
        has_permission=has_permission
    )


@permissions_bp.route('/<permission_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('permissions.edit')
def edit_permission(permission_id):
    """Edit permission"""
    permission = service.repository.get_permission_by_id(permission_id)
    if not permission:
        flash('Permission not found', 'danger')
        return redirect(url_for('permissions.permission_registry'))

    if request.method == 'POST':
        data = request.get_json()

        # Update permission
        permission, error = service.update_permission(permission_id, data)
        if error:
            return jsonify({'success': False, 'errors': [error]}), 400

        return jsonify({'success': True, 'message': 'Permission updated successfully'}), 200

    detail = service.repository.get_permission_detail(permission_id)
    categories = service.get_all_categories()

    return render_template(
        'permissions/edit.html',
        permission=permission,
        detail=detail,
        categories=categories,
        has_permission=has_permission
    )


@permissions_bp.route('/<permission_id>/delete', methods=['POST'])
@login_required
@permission_required('permissions.delete')
def delete_permission(permission_id):
    """Delete permission"""
    success, error = service.delete_permission(permission_id)

    if not success:
        return jsonify({'success': False, 'errors': [error]}), 400

    return jsonify({'success': True, 'message': 'Permission deleted successfully'}), 200


# Permission Matrix Routes

@permissions_bp.route('/matrix', methods=['GET'])
@login_required
@permission_required('permissions.view')
def permission_matrix():
    """Permission matrix visualization"""
    role_id = request.args.get('role_id', type=str)
    matrix = service.get_permission_matrix(role_id=role_id)
    roles = Role.query.all() if has_permission('permissions.manage_roles') else []

    return render_template(
        'permissions/matrix.html',
        matrix=matrix,
        roles=roles,
        selected_role_id=role_id,
        has_permission=has_permission
    )


# Role Assignment Routes

@permissions_bp.route('/roles/<role_id>/permissions', methods=['GET'])
@login_required
@permission_required('permissions.view')
def role_permissions(role_id):
    """View permissions for a role"""
    role = Role.query.get(role_id)
    if not role:
        flash('Role not found', 'danger')
        return redirect(url_for('permissions.dashboard'))

    permissions_grouped = service.get_role_permissions_grouped(role_id)
    analytics = service.get_role_permission_analytics(role_id)

    return render_template(
        'permissions/role_permissions.html',
        role=role,
        permissions_grouped=permissions_grouped,
        analytics=analytics,
        has_permission=has_permission
    )


@permissions_bp.route('/roles/<role_id>/assign', methods=['POST'])
@login_required
@permission_required('permissions.assign')
def assign_permissions_to_role(role_id):
    """Assign permission to role"""
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

    return jsonify({'success': True, 'message': 'Permission assigned successfully'}), 200


@permissions_bp.route('/roles/<role_id>/revoke', methods=['POST'])
@login_required
@permission_required('permissions.revoke')
def revoke_permission_from_role(role_id):
    """Revoke permission from role"""
    data = request.get_json()
    permission_id = data.get('permission_id')

    success = service.revoke_permission_from_role(role_id, permission_id)
    if not success:
        return jsonify({'success': False, 'errors': ['Failed to revoke permission']}), 400

    return jsonify({'success': True, 'message': 'Permission revoked successfully'}), 200


# Workflow Access Routes

@permissions_bp.route('/workflows', methods=['GET'])
@login_required
@permission_required('permissions.view')
def workflow_access():
    """Workflow access management"""
    # Get workflow permissions
    from app.modules.roles.models import WorkflowPermission
    workflow_perms = WorkflowPermission.query.all()
    roles = Role.query.all()

    return render_template(
        'permissions/workflow_access.html',
        workflow_permissions=workflow_perms,
        roles=roles,
        has_permission=has_permission
    )


# Analytics Routes

@permissions_bp.route('/analytics', methods=['GET'])
@login_required
@permission_required('permissions.view')
def analytics():
    """Permission analytics dashboard"""
    analytics_data = service.get_permission_analytics()
    role_id = request.args.get('role_id', type=str)
    
    role_analytics = None
    if role_id:
        role_analytics = service.get_role_permission_analytics(role_id)

    roles = Role.query.all() if has_permission('permissions.manage_roles') else []

    return render_template(
        'permissions/analytics.html',
        analytics=analytics_data,
        role_analytics=role_analytics,
        roles=roles,
        selected_role_id=role_id,
        has_permission=has_permission
    )


# Audit & Security Routes

@permissions_bp.route('/audit', methods=['GET'])
@login_required
@permission_required('permissions.view_audit')
def audit_logs():
    """Permission audit logs"""
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

    total_pages = (total + limit - 1) // limit

    return render_template(
        'permissions/audit.html',
        audit_logs=audit_logs,
        total=total,
        page=page,
        total_pages=total_pages,
        has_permission=has_permission
    )


# Settings Routes

@permissions_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@permission_required('permissions.manage_settings')
def settings():
    """Permission settings"""
    if request.method == 'POST':
        # Handle settings update
        pass

    categories = service.get_all_categories()

    return render_template(
        'permissions/settings.html',
        categories=categories,
        has_permission=has_permission
    )


# AJAX/Search endpoints

@permissions_bp.route('/search', methods=['GET'])
@login_required
@permission_required('permissions.view')
def search_permissions():
    """Search permissions via AJAX"""
    query = request.args.get('q', '', type=str)
    limit = request.args.get('limit', 10, type=int)

    if not query:
        return jsonify([]), 200

    permissions, _ = service.search_permissions(query, limit=limit)

    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
    } for p in permissions]), 200


@permissions_bp.route('/roles', methods=['GET'])
@login_required
@permission_required('permissions.view')
def get_roles_list():
    """Get roles list for dropdowns"""
    roles = Role.query.filter_by(is_system=False).all()

    return jsonify([{
        'id': r.id,
        'name': r.name,
        'description': r.description,
    } for r in roles]), 200
