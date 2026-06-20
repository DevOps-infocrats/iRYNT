from app.modules.auth.models import User, Role
from app.modules.users.repository import UserRepository


class UserService:
    def __init__(self):
        self.repository = UserRepository()

    def get_company_choices(self):
        companies = self.repository.get_companies()
        return [('', 'Select company')] + [(company.id, f"{company.company_name} ({company.company_code})") for company in companies]

    def get_circle_choices(self, company_id=None):
        circles = self.repository.get_circles(company_id)
        return [('', 'Select circle')] + [(circle.id, f"{circle.circle_name} ({circle.circle_code})") for circle in circles]

    def get_client_choices(self, circle_id=None):
        clients = self.repository.get_clients(circle_id)
        return [('', 'Select client')] + [(client.id, f"{client.client_name} ({client.client_code})") for client in clients]

    def get_project_choices(self, client_id=None):
        projects = self.repository.get_projects(client_id)
        return [('', 'Select project')] + [(projects.id, f"{projects.project_name} ({projects.project_code})") for projects in projects]

    def get_subzone_choices(self, project_id=None):
        subzones = self.repository.get_subzones(project_id)
        return [('', 'Select subzone')] + [(subzone.id, f"{subzone.subzone_name} ({subzone.subzone_code})") for subzone in subzones]

    def get_role_choices(self):
        roles = self.repository.get_roles()
        return [('', 'Select role')] + [(role.id, role.name) for role in roles]

    def get_status_options(self):
        return [
            {'id': 'Active', 'label': 'Active'},
            {'id': 'Inactive', 'label': 'Inactive'},
            {'id': 'Online', 'label': 'Online'},
            {'id': 'Offline', 'label': 'Offline'},
            {'id': 'Suspended', 'label': 'Suspended'},
            {'id': 'Pending Verification', 'label': 'Pending Verification'},
            {'id': 'On Leave', 'label': 'On Leave'},
        ]

    def get_access_scope_options(self):
        return [
            {'id': 'corporate', 'label': 'Corporate'},
            {'id': 'circle', 'label': 'Circle'},
            {'id': 'project', 'label': 'Project'},
            {'id': 'subzone', 'label': 'Subzone'},
        ]

    def get_operational_type_options(self):
        return [
            {'id': 'field', 'label': 'Field Operations'},
            {'id': 'support', 'label': 'Support'},
            {'id': 'driver', 'label': 'Driver Operations'},
            {'id': 'admin', 'label': 'Admin Operations'},
        ]

    def search_users(self, filters, page, per_page):
        offset = (page - 1) * per_page
        users, total = self.repository.list_users(filters, offset, per_page)
        rows = [self.serialize_user_row(user) for user in users]
        return rows, total

    def get_filter_payload(self, filters):
        return {
            'companies': self.get_company_choices(),
            'circles': self.get_circle_choices(filters.get('company_id')),
            'clients': self.get_client_choices(filters.get('circle_id')),
            'projects': self.get_project_choices(filters.get('client_id')),
            'subzones': self.get_subzone_choices(filters.get('project_id')),
            'roles': self.get_role_choices(),
            'status_options': self.get_status_options(),
            'access_scopes': self.get_access_scope_options(),
            'operational_types': self.get_operational_type_options(),
        }

    def get_dashboard_metrics(self, filters=None):
        filters = filters or {}
        total_users = self.repository.count_users(filters)
        return [
            {'title': 'Total Users', 'value': total_users, 'icon': 'groups', 'trend': '+14%', 'description': 'Workforce identity records'},
            {'title': 'Active Users', 'value': self.repository.count_users({**filters, 'status': 'Active'}), 'icon': 'task_alt', 'trend': '+8%', 'description': 'Enabled operations staff'},
            {'title': 'Drivers', 'value': self.repository.count_by_role_name('driver'), 'icon': 'directions_car', 'trend': '+5%', 'description': 'Operation drivers count'},
            {'title': 'Helpers', 'value': self.repository.count_by_role_name('helper'), 'icon': 'support_agent', 'trend': '+2%', 'description': 'Support workforce count'},
            {'title': 'Online Users', 'value': self.repository.count_online_users(filters), 'icon': 'wifi', 'trend': '+19%', 'description': 'Realtime logged-in staff'},
            {'title': 'Deployed Users', 'value': self.repository.count_deployed_users(), 'icon': 'rocket_launch', 'trend': '+7%', 'description': 'Users with active deployment'},
            {'title': 'Pending Verification', 'value': self.repository.count_pending_verification(filters), 'icon': 'pending', 'trend': '-3%', 'description': 'Identity verification queue'},
            {'title': 'Suspended Users', 'value': self.repository.count_suspended(filters), 'icon': 'block', 'trend': '-1%', 'description': 'Temporarily blocked accounts'},
        ]

    def serialize_user_row(self, user):
        assigned_vehicle = self.repository.find_assigned_vehicle(user)
        online = self.repository.is_user_online(user)
        attendance_status = 'Checked In' if online else 'Absent'
        deployment_status = 'Deployed' if assigned_vehicle and assigned_vehicle.current_deployment else 'Ready' if assigned_vehicle else 'Unassigned'
        operational_state = 'On Duty' if online else 'Offline' if user.is_active else 'Suspended'
        return {
            'id': user.id,
            'employee_id': user.id[:8].upper(),
            'name': user.username,
            'email': user.email,
            'phone': user.phone or 'N/A',
            'role': user.primary_role.name if user.primary_role else 'Unassigned',
            'hierarchy': {
                'company': self.repository.get_company_name(user.company_id),
                'circle': self.repository.get_circle_name(user.circle_id),
                'project': 'N/A',
                'subzone': 'N/A',
            },
            'assigned_vehicle': assigned_vehicle.vehicle_number if assigned_vehicle else 'Unassigned',
            'attendance_status': attendance_status,
            'deployment_status': deployment_status,
            'operational_status': operational_state,
            'online': online,
            'verified': user.is_verified,
            'active': user.is_active,
            'last_activity': user.last_login_at.isoformat() if user.last_login_at else None,
            'permissions': user.permissions,
        }

    def get_user(self, user_id):
        return self.repository.get_user_by_id(user_id)

    def create_user(self, payload):
        role_id = payload.get('role_id')
        company_id = payload.get('company_id')
        circle_id = payload.get('circle_id')
        project_id = payload.get('project_id')
        password = payload.get('password') or 'ChangeMe@123'
        user = User(
            username=payload['username'],
            email=payload['email'],
            phone=payload.get('phone'),
            company_id=company_id,
            circle_id=circle_id,
            is_active=payload.get('is_active', True),
            is_verified=payload.get('is_verified', True),
        )
        user.set_password(password)
        if role_id:
            role = Role.query.get(role_id)
            if role:
                user.primary_role = role
                user.roles = [role]

        from app.extensions import db
        db.session.add(user)
        db.session.commit()
        ensure_helper_profile(user, project_id=project_id)
        
        # Safe welcome notification
        try:
            from app.modules.notifications.helpers import create_notification_safe
            create_notification_safe(
                user_id=user.id,
                message=f"Welcome to VIL Workforce Management! Your account ({user.username}) is active.",
                module="system",
                priority="info",
                type="system"
            )
        except Exception:
            pass

        return user

    def update_user(self, user_id, payload):
        user = self.repository.get_user_by_id(user_id)
        if not user:
            return None
        user.username = payload['username']
        user.email = payload['email']
        user.phone = payload.get('phone')
        user.company_id = payload.get('company_id')
        user.circle_id = payload.get('circle_id')
        user.is_active = payload.get('is_active', True)
        user.is_verified = payload.get('is_verified', False)

        password = payload.get('password')
        if password:
            user.set_password(password)

        role_id = payload.get('role_id')
        if role_id:
            role = Role.query.get(role_id)
            if role:
                user.primary_role = role
                user.roles = [role]

        from app.extensions import db
        db.session.commit()
        ensure_helper_profile(user, project_id=payload.get('project_id'))
        return user

    def get_user_profile(self, user_id):
        user = self.repository.get_user_by_id(user_id)
        if not user:
            return None

        assigned_vehicle = self.repository.find_assigned_vehicle(user)
        online = self.repository.is_user_online(user)
        attendance_history = self.repository.get_login_history(user)
        role_level = user.role_level if hasattr(user, 'role_level') else 0
        permissions = user.permissions if hasattr(user, 'permissions') else []

        return {
            'user': user,
            'online': online,
            'assigned_vehicle': assigned_vehicle,
            'attendance_status': 'Checked In' if online else 'Absent',
            'deployment_status': 'Deployed' if assigned_vehicle and assigned_vehicle.current_deployment else 'Ready' if assigned_vehicle else 'Unassigned',
            'operational_status': 'On Duty' if online else 'Offline' if user.is_active else 'Suspended',
            'hierarchy': {
                'company': self.repository.get_company_name(user.company_id),
                'circle': self.repository.get_circle_name(user.circle_id),
                'client': 'N/A',
                'project': 'N/A',
                'subzone': 'N/A',
            },
            'permissions': permissions,
            'approval_rights': 'Granted' if role_level >= 10 else 'Limited',
            'attendance_history': [
                {
                    'event': 'Login' if event.success else 'Failed Sign-In',
                    'timestamp': event.created_at.strftime('%Y-%m-%d %H:%M'),
                    'note': event.reason or ('Checked in successfully' if event.success else 'Authentication failure'),
                }
                for event in attendance_history
            ],
            'analytics': {
                'attendance_labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'attendance_values': self.repository.get_weekly_successful_login_percentages(user, days=7),
                'role_labels': [row[0] for row in self.repository.get_role_distribution()[:6]],
                'role_values': [int(row[1]) for row in self.repository.get_role_distribution()[:6]],
            },
        }

    def get_hierarchy_options(self, option_type, parent_id=None):
        if option_type == 'circle':
            return [{'id': circle.id, 'text': f"{circle.circle_name} ({circle.circle_code})"} for circle in self.repository.get_circles(parent_id)]
        if option_type == 'client':
            return [{'id': client.id, 'text': f"{client.client_name} ({client.client_code})"} for client in self.repository.get_clients(parent_id)]
        if option_type == 'project':
            return [{'id': project.id, 'text': f"{project.project_name} ({project.project_code})"} for project in self.repository.get_projects(parent_id)]
        if option_type == 'subzone':
            return [{'id': subzone.id, 'text': f"{subzone.subzone_name} ({subzone.subzone_code})"} for subzone in self.repository.get_subzones(parent_id)]
        return []

    def search_suggestions(self, query_text):
        if not query_text:
            return []

        results, _ = self.repository.list_users({'search_query': query_text}, 0, 10)
        return [
            {
                'id': item['id'],
                'name': item['name'],
                'email': item['email'],
                'role': item['role'],
                'vehicle': item['assigned_vehicle'],
            }
            for item in results
        ]


def ensure_helper_profile(user, project_id=None):
    from app.modules.auth.models import Role
    from app.modules.drivers.models import DriverProfile
    from app.modules.circles.models import Circle
    from app.modules.clients.models import Client
    from app.modules.projects.models import Project
    from app.modules.subzones.models import Subzone
    from app.extensions import db
    import uuid

    is_helper = False
    is_driver = False
    if user.primary_role:
        if user.primary_role.name == 'Helper':
            is_helper = True
        elif user.primary_role.name == 'Driver':
            is_driver = True
    for r in user.roles:
        if r.name == 'Helper':
            is_helper = True
        elif r.name == 'Driver':
            is_driver = True

    if not (is_helper or is_driver):
        return None

    profile = DriverProfile.query.filter_by(user_id=user.id).first()
    company_id = user.company_id
    circle_id = user.circle_id

    target_project_id = project_id
    target_client_id = None

    if target_project_id:
        p = Project.query.get(target_project_id)
        if p:
            target_client_id = p.client_id
            if not company_id:
                company_id = p.company_id
            if not circle_id:
                circle_id = p.circle_id

    target_circle_id = circle_id
    if not target_circle_id and company_id:
        c = Circle.query.filter_by(company_id=company_id).first()
        if c:
            target_circle_id = c.id

    if not target_client_id:
        if company_id and target_circle_id:
            cl = Client.query.filter_by(company_id=company_id, circle_id=target_circle_id).first()
            if cl:
                target_client_id = cl.id

    if not target_project_id:
        if company_id and target_circle_id and target_client_id:
            p = Project.query.filter_by(company_id=company_id, circle_id=target_circle_id, client_id=target_client_id).first()
            if p:
                target_project_id = p.id

    target_subzone_id = None
    if company_id and target_circle_id and target_client_id and target_project_id:
        sz = Subzone.query.filter_by(company_id=company_id, circle_id=target_circle_id, client_id=target_client_id, project_id=target_project_id).first()
        if sz:
            target_subzone_id = sz.id

    if not profile:
        prefix = "HLP" if is_helper else "DRV"
        driver_code = f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
        profile = DriverProfile(
            user_id=user.id,
            driver_code=driver_code,
            circle_id=target_circle_id,
            client_id=target_client_id,
            project_id=target_project_id,
            subzone_id=target_subzone_id,
            active=True,
            license_status='Approved',
            compliance_status='Compliant',
        )
        db.session.add(profile)
    else:
        if not profile.circle_id:
            profile.circle_id = target_circle_id
        if not profile.client_id:
            profile.client_id = target_client_id
        if not profile.project_id:
            profile.project_id = target_project_id
        if not profile.subzone_id:
            profile.subzone_id = target_subzone_id

    db.session.commit()
    return profile
