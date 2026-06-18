from sqlalchemy import or_, and_, func
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.modules.auth.models import LoginAttempt, Role, User, UserSession
from app.modules.vehicles.models import Vehicle
from app.modules.companies.models import Company
from app.modules.circles.models import Circle
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.subzones.models import Subzone


class UserRepository:
    def base_query(self):
        return User.query.options(joinedload(User.primary_role)).options(joinedload(User.roles))

    def _apply_filters(self, query, filters):
        if filters.get('company_id'):
            query = query.filter(User.company_id == filters['company_id'])
        if filters.get('circle_id'):
            query = query.filter(User.circle_id == filters['circle_id'])
        if filters.get('role_id'):
            query = query.filter(
                or_(
                    User.role_id == filters['role_id'],
                    User.roles.any(Role.id == filters['role_id']),
                )
            )
        if filters.get('status'):
            status = filters['status']
            if status == 'Active':
                query = query.filter(User.is_active.is_(True))
            elif status == 'Inactive':
                query = query.filter(User.is_active.is_(False))
            elif status == 'Online':
                query = query.filter(User.sessions.any(and_(UserSession.active.is_(True), UserSession.revoked.is_(False))))
            elif status == 'Offline':
                query = query.filter(~User.sessions.any(and_(UserSession.active.is_(True), UserSession.revoked.is_(False))), User.is_active.is_(True))
            elif status == 'Suspended':
                query = query.filter(User.is_active.is_(False))
            elif status == 'Pending Verification':
                query = query.filter(User.is_verified.is_(False))
            elif status == 'On Leave':
                query = query.filter(User.is_active.is_(False))

        if filters.get('search_query'):
            search_value = f"%{filters['search_query']}%"
            matching_users = User.query.filter(
                or_(
                    User.username.ilike(search_value),
                    User.email.ilike(search_value),
                    User.phone.ilike(search_value),
                    User.id.ilike(search_value),
                )
            ).with_entities(User.id).limit(300).all()
            user_ids = {item.id for item in matching_users}

            vehicle_matches = Vehicle.query.filter(Vehicle.vehicle_number.ilike(search_value)).with_entities(Vehicle.assigned_driver).limit(100).all()
            for row in vehicle_matches:
                if row.assigned_driver:
                    matched_users = User.query.filter(User.username == row.assigned_driver).with_entities(User.id).all()
                    user_ids.update([u.id for u in matched_users])

            if user_ids:
                query = query.filter(User.id.in_(list(user_ids)))
            else:
                query = query.filter(False)

        return query

    def list_users(self, filters, offset, limit):
        query = self._apply_filters(self.base_query(), filters)
        # Use distinct() without column argument to avoid DISTINCT ON issues with ORDER BY
        total = query.distinct().count()
        users = (
            query.order_by(User.id, User.username)
            .offset(offset)
            .limit(limit)
            .all()
        )
        return users, total

    def get_user_by_id(self, user_id):
        return self.base_query().filter(User.id == user_id).first()

    def find_assigned_vehicle(self, user):
        if not user or not user.username:
            return None
        return (
            Vehicle.query.filter(Vehicle.assigned_driver == user.username)
            .order_by(Vehicle.updated_at.desc())
            .first()
        )

    def is_user_online(self, user):
        return UserSession.query.filter_by(user_id=user.id, active=True, revoked=False).count() > 0

    def get_companies(self):
        return Company.query.filter_by(status='Active').order_by(Company.company_name).all()

    def get_circles(self, company_id=None):
        query = Circle.query.order_by(Circle.circle_name)
        if company_id:
            query = query.filter_by(company_id=company_id)
        return query.all()

    def get_clients(self, circle_id=None):
        query = Client.query.order_by(Client.client_name)
        if circle_id:
            query = query.filter_by(circle_id=circle_id)
        return query.all()

    def get_projects(self, client_id=None):
        query = Project.query.order_by(Project.project_name)
        if client_id:
            query = query.filter_by(client_id=client_id)
        return query.all()

    def get_subzones(self, project_id=None):
        query = Subzone.query.order_by(Subzone.subzone_name)
        if project_id:
            query = query.filter_by(project_id=project_id)
        return query.all()

    def get_roles(self):
        return Role.query.order_by(Role.name).all()

    def get_company_name(self, company_id):
        if not company_id:
            return 'Global'
        company = Company.query.get(company_id)
        return company.company_name if company else 'Global'

    def get_circle_name(self, circle_id):
        if not circle_id:
            return 'Shared'
        circle = Circle.query.get(circle_id)
        return circle.circle_name if circle else 'Shared'

    def count_users(self, filters=None):
        query = self._apply_filters(self.base_query(), filters or {})
        return query.distinct().count()

    def count_online_users(self, filters=None):
        query = self._apply_filters(self.base_query(), filters or {})
        query = query.filter(User.sessions.any(and_(UserSession.active.is_(True), UserSession.revoked.is_(False))))
        return query.distinct().count()

    def count_by_role_name(self, role_name):
        return self.base_query().filter(
            or_(
                User.primary_role.has(Role.name.ilike(role_name)),
                User.roles.any(Role.name.ilike(role_name)),
            )
        ).distinct().count()

    def count_pending_verification(self, filters=None):
        query = self._apply_filters(self.base_query(), filters or {})
        return query.filter(User.is_verified.is_(False)).distinct().count()

    def count_suspended(self, filters=None):
        query = self._apply_filters(self.base_query(), filters or {})
        return query.filter(User.is_active.is_(False)).distinct(User.id).count()

    def count_deployed_users(self):
        return (
            User.query.join(Vehicle, Vehicle.assigned_driver == User.username)
            .filter(Vehicle.current_deployment.isnot(None))
            .distinct(User.id)
            .count()
        )

    def get_login_history(self, user, limit=6):
        if not user:
            return []
        return (
            LoginAttempt.query.filter_by(user_id=user.id)
            .order_by(LoginAttempt.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_weekly_successful_login_percentages(self, user, days=7):
        """Return a list of percentages (0-100) representing successful login activity
        for the past `days` days for the given user. Uses simple scaling relative to
        the day with the highest count to produce percentage values suitable for charts.
        """
        from datetime import datetime, timedelta, timezone

        if not user:
            return [0] * days

        now = datetime.now(timezone.utc)
        start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
        attempts = (
            LoginAttempt.query.filter_by(user_id=user.id, success=True)
            .filter(LoginAttempt.created_at >= start)
            .with_entities(LoginAttempt.created_at)
            .all()
        )

        counts = [0] * days
        for (dt,) in attempts:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            delta = (dt.date() - start.date()).days
            if 0 <= delta < days:
                counts[delta] += 1

        max_count = max(counts) if counts else 0
        if max_count == 0:
            return [0] * days
        return [round((c / max_count) * 100) for c in counts]

    def get_role_distribution(self):
        return (
            db.session.query(Role.name, func.count(User.id).label('count'))
            .join(User, User.role_id == Role.id)
            .group_by(Role.name)
            .all()
        )

