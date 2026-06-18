from flask_login import current_user

from app.domain.auth.policies.auth_policy import has_permission, has_role


SIDEBAR_MENU = [
    {
        'key': 'dashboard',
        'title': 'Dashboard',
        'icon': 'dashboard',
        'children': [
            {
                'id': 'dashboard-overview',
                'key': 'overview',
                'title': 'Dashboard Overview',
                'endpoint': 'auth.dashboard',
                'page': 'dashboard',
                'icon': 'dashboard',
            },
        ],
    },
    {
        'key': 'masters',
        'title': 'Masters',
        'icon': 'storage',
        'children': [
            {
                'id': 'masters-company',
                'key': 'company',
                'title': 'Company',
                'endpoint': 'companies.index',
                'permission': 'companies.view',
                'page': 'companies',
                'icon': 'business',
            },
            {
                'id': 'masters-circle',
                'key': 'circle',
                'title': 'Circle',
                'endpoint': 'circles.index',
                'permission': 'circles.view',
                'page': 'circles',
                'icon': 'public',
            },
            {
                'id': 'masters-client',
                'key': 'client',
                'title': 'Client',
                'endpoint': 'clients.index',
                'permission': 'clients.view',
                'page': 'clients',
                'icon': 'handshake',
            },
            {
                'id': 'masters-project',
                'key': 'project',
                'title': 'Project',
                'endpoint': 'projects.index',
                'permission': 'projects.view',
                'page': 'projects',
                'icon': 'work_outline',
            },
            {
                'id': 'masters-subzone',
                'key': 'subzone',
                'title': 'Subzone',
                'endpoint': 'subzones.index',
                'permission': 'subzones.view',
                'page': 'subzones',
                'icon': 'map',
            },
            {
                'id': 'masters-vehicle',
                'key': 'vehicle_master',
                'title': 'Vehicle Master',
                'endpoint': 'vehicles.index',
                'permission': 'vehicles.view',
                'page': 'vehicle_master',
                'icon': 'directions_bus',
            },
        ],
    },
    {
        'key': 'user_management',
        'title': 'User Management',
        'icon': 'groups',
        'children': [
            {
                'id': 'users-list',
                'key': 'users',
                'title': 'Users',
                'endpoint': 'users.index',
                'permission': 'users.view',
                'page': 'users',
                'icon': 'person',
            },
            {
                'id': 'roles-list',
                'key': 'roles',
                'title': 'Roles',
                'endpoint': 'roles.index',
                'permission': 'roles.view',
                'page': 'roles',
                'icon': 'security',
            },
            {
                'id': 'permissions-list',
                'key': 'permissions',
                'title': 'Permissions',
                'endpoint': 'permissions.dashboard',
                'permission': 'permissions.view',
                'page': 'permissions',
                'icon': 'shield',
            },
            {
                'id': 'driver-profiles',
                'key': 'driver_profiles',
                'title': 'Driver Profiles',
                'endpoint': 'drivers.index',
                'permission': 'driver_profiles.view',
                'page': 'driver_profiles',
                'icon': 'badge',
            },
            {
                'id': 'access-control',
                'key': 'access_control',
                'title': 'Access Control',
                'endpoint': 'access_control.index',
                'permission': 'access_control.view',
                'page': 'access_control',
                'icon': 'lock',
            },
        ],
    },
    {
        'key': 'deployments',
        'title': 'Deployments',
        'icon': 'local_shipping',
        'children': [
            {
                'id': 'deployments-vehicle',
                'key': 'vehicle_deployment',
                'title': 'Vehicle Deployment',
                'endpoint': 'deployments.index',
                'permission': 'deployments.view',
                'page': 'deployments',
                'icon': 'local_shipping',
            },
            {
                'id': 'deployments-assignment',
                'key': 'driver_assignment',
                'title': 'Driver Assignment',
                'endpoint': 'deployments.assignment_dashboard',
                'permission': 'deployments.assign',
                'page': 'driver_assignment',
                'icon': 'assignment_ind',
            },
            {
                'id': 'deployments-helper-assignment',
                'key': 'helper_assignment',
                'title': 'Helper Assignment',
                'endpoint': 'deployments.helper_assignments_index',
                'permission': 'helper_assignments.view',
                'page': 'helper_assignments',
                'icon': 'assignment_ind',
            },
            {
                'id': 'deployments-active',
                'key': 'active_deployments',
                'title': 'Active Deployments',
                'endpoint': 'deployments.active',
                'permission': 'deployments.active.view',
                'page': 'deployments_active',
                'icon': 'speed',
            },
            {
                'id': 'deployments-history',
                'key': 'deployment_history',
                'title': 'Deployment History',
                'endpoint': 'deployments.history',
                'permission': 'deployments.history.view',
                'page': 'deployments_history',
                'icon': 'history',
            },
        ],
    },
    {
        'key': 'attendance',
        'title': 'Attendance',
        'icon': 'calendar_month',
        'children': [
            {
                'id': 'attendance-live',
                'key': 'live_attendance',
                'title': 'Live Attendance',
                'endpoint': 'attendance.live',
                'permission': 'attendance.view',
                'page': 'live_attendance',
                'icon': 'schedule',
            },
            {
                'id': 'attendance-history',
                'key': 'attendance_history',
                'title': 'Attendance History',
                'endpoint': 'attendance.history',
                'permission': 'attendance.history.view',
                'page': 'attendance_history',
                'icon': 'history_edu',
            },
            {
                'id': 'attendance-monitoring',
                'key': 'check_in_monitoring',
                'title': 'Check-In Monitoring',
                'endpoint': 'attendance.monitoring',
                'permission': 'attendance.monitoring.view',
                'page': 'check_in_monitoring',
                'icon': 'monitoring',
            },
            {
                'id': 'attendance-approvals',
                'key': 'attendance_approvals',
                'title': 'Attendance Approvals',
                'endpoint': 'attendance.approvals',
                'permission': 'attendance.approvals.view',
                'page': 'attendance_approvals',
                'icon': 'thumb_up',
            },
            {
                'id': 'attendance-shift-reports',
                'key': 'shift_reports',
                'title': 'Shift Reports',
                'endpoint': 'attendance.shift_reports',
                'permission': 'attendance.reports.view',
                'page': 'shift_reports',
                'icon': 'description',
            },
        ],
    },
    {
        'key': 'documents',
        'title': 'Document Management',
        'icon': 'folder_shared',
        'children': [
            {
                'id': 'documents-vehicle',
                'key': 'vehicle_documents',
                'title': 'Vehicle Documents',
                'endpoint': 'documents.vehicles',
                'permission': 'documents.view',
                'page': 'vehicle_documents',
                'icon': 'directions_car',
            },
            {
                'id': 'documents-driver',
                'key': 'driver_documents',
                'title': 'Driver Documents',
                'endpoint': 'documents.drivers',
                'permission': 'documents.view',
                'page': 'driver_documents',
                'icon': 'badge',
            },
            {
                'id': 'documents-expiry',
                'key': 'expiry_tracking',
                'title': 'Expiry Tracking',
                'endpoint': 'documents.expiry',
                'permission': 'documents.expiry.view',
                'page': 'expiry_tracking',
                'icon': 'timer',
            },
            {
                'id': 'documents-pending',
                'key': 'pending_verification',
                'title': 'Pending Verification',
                'endpoint': 'documents.pending',
                'permission': 'documents.pending.view',
                'page': 'pending_verification',
                'icon': 'pending',
            },
            {
                'id': 'documents-approvals',
                'key': 'document_approvals',
                'title': 'Document Approvals',
                'endpoint': 'documents.approvals',
                'permission': 'documents.approvals.view',
                'page': 'document_approvals',
                'icon': 'check_circle',
            },
        ],
    },
    {
        'key': 'reports',
        'title': 'Reports & Analytics',
        'icon': 'bar_chart',
        'children': [
            {
                'id': 'reports-attendance',
                'key': 'attendance_reports',
                'title': 'Attendance Reports',
                'endpoint': 'reports.attendance',
                'permission': 'reports.view',
                'page': 'attendance_reports',
                'icon': 'calendar_view_month',
            },
            {
                'id': 'reports-deployments',
                'key': 'deployment_reports',
                'title': 'Deployment Reports',
                'endpoint': 'reports.deployments',
                'permission': 'reports.view',
                'page': 'deployment_reports',
                'icon': 'local_shipping',
            },
            {
                'id': 'reports-vehicle',
                'key': 'vehicle_reports',
                'title': 'Vehicle Reports',
                'endpoint': 'reports.vehicles',
                'permission': 'reports.view',
                'page': 'vehicle_reports',
                'icon': 'directions_bus',
            },
            {
                'id': 'reports-mis',
                'key': 'mis_reports',
                'title': 'MIS Reports',
                'endpoint': 'reports.mis',
                'permission': 'reports.view',
                'page': 'mis_reports',
                'icon': 'insights',
            },
            {
                'id': 'reports-export',
                'key': 'export_center',
                'title': 'Export Center',
                'endpoint': 'reports.export',
                'permission': 'reports.export',
                'page': 'export_center',
                'icon': 'file_download',
            },
            {
                'id': 'reports-analytics',
                'key': 'operational_analytics',
                'title': 'Operational Analytics',
                'endpoint': 'analytics.index',
                'permission': 'analytics.view',
                'page': 'operational_analytics',
                'icon': 'stacked_line_chart',
            },
        ],
    },
    {
        'key': 'workflows',
        'title': 'Workflows & Approvals',
        'icon': 'workflow',
        'children': [
            {
                'id': 'workflows-pending',
                'key': 'pending_approvals',
                'title': 'Pending Approvals',
                'endpoint': 'approvals.index',
                'permission': 'workflows.view',
                'page': 'pending_approvals',
                'icon': 'pending_actions',
            },
            {
                'id': 'workflows-queue',
                'key': 'workflow_queue',
                'title': 'Workflow Queue',
                'endpoint': 'approvals.index',
                'permission': 'workflows.view',
                'page': 'workflow_queue',
                'icon': 'view_list',
            },
            {
                'id': 'workflows-history',
                'key': 'approval_history',
                'title': 'Approval History',
                'endpoint': 'approvals.index',
                'permission': 'workflows.view',
                'page': 'approval_history',
                'icon': 'history',
            },
            {
                'id': 'workflows-escalations',
                'key': 'escalations',
                'title': 'Escalations',
                'endpoint': 'approvals.index',
                'permission': 'workflows.view',
                'page': 'escalations',
                'icon': 'notification_important',
            },
        ],
    },
    {
        'key': 'realtime',
        'title': 'Real-Time Operations',
        'icon': 'traffic',
        'children': [
            {
                'id': 'realtime-vehicle',
                'key': 'live_vehicle_status',
                'title': 'Live Vehicle Status',
                'endpoint': 'realtime.vehicles',
                'permission': 'realtime.view',
                'page': 'live_vehicle_status',
                'icon': 'directions_car',
            },
            {
                'id': 'realtime-driver',
                'key': 'live_driver_tracking',
                'title': 'Live Driver Tracking',
                'endpoint': 'realtime.drivers',
                'permission': 'realtime.view',
                'page': 'live_driver_tracking',
                'icon': 'navigation',
            },
            {
                'id': 'realtime-heatmap',
                'key': 'operational_heatmap',
                'title': 'Operational Heatmap',
                'endpoint': 'realtime.heatmap',
                'permission': 'realtime.view',
                'page': 'operational_heatmap',
                'icon': 'heat_pump',
            },
            {
                'id': 'realtime-subzones',
                'key': 'active_subzones',
                'title': 'Active Subzones',
                'endpoint': 'realtime.subzones',
                'permission': 'realtime.view',
                'page': 'active_subzones',
                'icon': 'map',
            },
            {
                'id': 'realtime-incidents',
                'key': 'incident_monitoring',
                'title': 'Incident Monitoring',
                'endpoint': 'realtime.incidents',
                'permission': 'realtime.view',
                'page': 'incident_monitoring',
                'icon': 'report_problem',
            },
        ],
    },
    {
        'key': 'notifications',
        'title': 'Notifications',
        'icon': 'notifications',
        'children': [
            {
                'id': 'notifications-system',
                'key': 'system_notifications',
                'title': 'System Notifications',
                'endpoint': 'notifications.system_notifications',
                'permission': 'notifications.view',
                'page': 'system_notifications',
                'icon': 'notifications_active',
            },
            {
                'id': 'notifications-expiry',
                'key': 'expiry_alerts',
                'title': 'Expiry Alerts',
                'endpoint': 'notifications.expiry_alerts',
                'permission': 'notifications.view',
                'page': 'expiry_alerts',
                'icon': 'alarm',
            },
            {
                'id': 'notifications-attendance',
                'key': 'attendance_alerts',
                'title': 'Attendance Alerts',
                'endpoint': 'notifications.attendance_alerts',
                'permission': 'notifications.view',
                'page': 'attendance_alerts',
                'icon': 'calendar_today',
            },
            {
                'id': 'notifications-deployment',
                'key': 'deployment_alerts',
                'title': 'Deployment Alerts',
                'endpoint': 'notifications.deployment_alerts',
                'permission': 'notifications.view',
                'page': 'deployment_alerts',
                'icon': 'local_shipping',
            },
        ],
    },
    {
        'key': 'audit_security',
        'title': 'Audit & Security',
        'icon': 'shield',
        'children': [
            {
                'id': 'audit-logs',
                'key': 'audit_logs',
                'title': 'Audit Logs',
                'endpoint': 'audit_logs.index',
                'permission': 'audit_logs.view',
                'page': 'audit_logs',
                'icon': 'history',
            },
            {
                'id': 'login-activity',
                'key': 'login_activity',
                'title': 'Login Activity',
                'endpoint': 'security.activity',
                'permission': 'security.activity.view',
                'page': 'login_activity',
                'icon': 'login',
            },
            {
                'id': 'access-logs',
                'key': 'access_logs',
                'title': 'Access Logs',
                'endpoint': 'security.access_logs',
                'permission': 'security.access_logs.view',
                'page': 'access_logs',
                'icon': 'vpn_key',
            },
        ],
    },
    {
        'key': 'settings',
        'title': 'Settings',
        'icon': 'settings',
        'children': [
            {
                'id': 'settings-general',
                'key': 'general_settings',
                'title': 'General Settings',
                'endpoint': 'settings.general',
                'permission': 'settings.view',
                'page': 'general_settings',
                'icon': 'tune',
            },
        ],
    },
]


def _item_visible(item):
    if item.get('permission') and not has_permission(item['permission']):
        return False
    roles = item.get('roles')
    if roles:
        if isinstance(roles, (list, tuple, set)):
            return any(has_role(role) for role in roles)
        return has_role(roles)
    return True


def _is_driver_role():
    """Check if the current user has ONLY the Driver or Helper role (not admin)."""
    # Only restrict if user is a driver/helper and NOT an admin role
    is_field = has_role('Driver') or has_role('Helper')
    is_admin = has_role('Super Admin') or has_role('Admin')
    return is_field and not is_admin


def _filter_items_for_driver(items):
    """Filter menu items for driver/helper - only show allowed items."""
    allowed_item_keys = {
        'live_attendance',  # Mark Attendance
        'vehicle_deployment',  # Vehicle Deployment
        'active_deployments',  # Active Deployments
        'helper_assignment',  # Helper Assignment
    }
    filtered = []
    for item in items:
        if item.get('key') in allowed_item_keys and _item_visible(item):
            clone = item.copy()
            if clone.get('key') == 'live_attendance':
                clone['title'] = 'Mark Attendance'
            filtered.append(clone)
    return filtered


def _filter_items(items):
    """Standard filtering for non-driver users."""
    filtered = []
    for item in items:
        if item.get('children'):
            children = _filter_items(item['children'])
            if children:
                clone = item.copy()
                clone['children'] = children
                filtered.append(clone)
        elif _item_visible(item):
            filtered.append(item)
    return filtered


def build_sidebar_menu():
    """Build the sidebar menu, filtering based on user role and permissions."""
    is_driver = _is_driver_role()
    
    # For drivers, show only Deployments and Attendance sections
    if is_driver:
        allowed_sections = {'deployments', 'attendance'}
        result = []
        for section in SIDEBAR_MENU:
            if section['key'] in allowed_sections:
                filtered_children = _filter_items_for_driver(section.get('children', []))
                if filtered_children:
                    result.append({
                        'key': section['key'],
                        'title': section['title'],
                        'icon': section.get('icon'),
                        'children': filtered_children,
                    })
        return result
    
    # Standard menu for non-drivers
    return [
        {
            'key': section['key'],
            'title': section['title'],
            'icon': section.get('icon'),
            'children': _filter_items(section.get('children', [])),
        }
        for section in SIDEBAR_MENU
        if _filter_items(section.get('children', []))
    ]
