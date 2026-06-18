from flask import Blueprint, render_template
from flask_login import login_required

from app.core.decorators import permission_required
from app.modules.permissions.services import PermissionService
from app.modules.roles.services import RolesService

access_control_bp = Blueprint('access_control', __name__, url_prefix='/access-control')

roles_service = RolesService()
permission_service = PermissionService()


@access_control_bp.route('/', methods=['GET'])
@login_required
@permission_required('access_control.view')
def index():
    """Access Control overview dashboard"""
    role_stats = roles_service.get_dashboard_kpis()
    permission_stats = permission_service.get_dashboard_kpis()

    kpis = [
        {
            'title': 'Total Roles',
            'value': role_stats[0]['value'],
            'icon': 'security',
            'description': 'All roles configured in the system.',
        },
        {
            'title': 'Total Permissions',
            'value': permission_stats['total_permissions'],
            'icon': 'shield',
            'description': 'Permissions available for access control.',
        },
        {
            'title': 'Active Roles',
            'value': role_stats[1]['value'],
            'icon': 'verified_user',
            'description': 'Roles currently assigned to users.',
        },
        {
            'title': 'Workflow Authorities',
            'value': permission_stats['workflow_permissions'],
            'icon': 'workflow',
            'description': 'Approval and workflow access rules.',
        },
        {
            'title': 'Restricted Permissions',
            'value': permission_stats['restricted_permissions'],
            'icon': 'shield_moon',
            'description': 'High-security permissions in use.',
        },
        {
            'title': 'Assigned Roles',
            'value': permission_stats['assigned_roles'],
            'icon': 'groups',
            'description': 'Roles configured for the permission store.',
        },
    ]

    return render_template(
        'access_control/index.html',
        kpis=kpis,
        active_page='access_control',
    )
