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
from app.modules.attendance.utils import get_india_today
from app.modules.drivers.models import (
    DriverProfile,
    DriverLicense,
    DriverDocument,
    DriverVehicleAssignment,
    DriverAttendance,
    DriverTrip,
    DriverPerformance,
    DriverIncident,
    DriverPayroll,
    DriverActivityLog,
)


class DriverRepository:
    def driver_base_query(self):
        return User.query.options(joinedload(User.primary_role), joinedload(User.driver_profile))

    def _driver_role_filter(self, query):
        return query.filter(
            or_(
                User.primary_role.has(Role.name.ilike('driver')),
                User.roles.any(Role.name.ilike('driver')),
            )
        )

    def _apply_filters(self, query, filters):
        query = self._driver_role_filter(query)

        if filters.get('company_id'):
            query = query.filter(User.company_id == filters['company_id'])
        if filters.get('circle_id'):
            query = query.filter(User.circle_id == filters['circle_id'])
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

        if filters.get('search_query'):
            search_value = f"%{filters['search_query']}%"
            matching_users = (
                User.query.filter(
                    or_(
                        User.username.ilike(search_value),
                        User.email.ilike(search_value),
                        User.phone.ilike(search_value),
                        User.id.ilike(search_value),
                    )
                )
                .with_entities(User.id)
                .limit(300)
                .all()
            )
            user_ids = {item.id for item in matching_users}

            vehicle_matches = (
                Vehicle.query.filter(Vehicle.vehicle_number.ilike(search_value))
                .with_entities(Vehicle.assigned_driver)
                .limit(100)
                .all()
            )
            for row in vehicle_matches:
                if row.assigned_driver:
                    driver = User.query.filter(User.username == row.assigned_driver).with_entities(User.id).first()
                    if driver:
                        user_ids.add(driver.id)

            if user_ids:
                query = query.filter(User.id.in_(list(user_ids)))
            else:
                query = query.filter(False)

        return query

    def list_drivers(self, filters, offset, limit):
        query = self._apply_filters(self.driver_base_query(), filters)
        total = query.distinct().count()

        drivers = (
            query.order_by(User.username)
            .offset(offset)
            .limit(limit)
            .all()
        )

        assigned_map = self._get_assigned_vehicle_map(drivers)
        rows = [
            self.serialize_driver_row(
                user,
                assigned_map.get(user.id) or assigned_map.get(user.username),
            )
            for user in drivers
        ]
        return rows, total

    def get_driver_by_id(self, user_id):
        return self.driver_base_query().filter(User.id == user_id).first()

    def get_driver_profile(self, user_id):
        user = self.get_driver_by_id(user_id)
        if not user:
            return None

        driver_profile = DriverProfile.query.filter_by(user_id=user.id).first()
        assigned_vehicle = self.find_assigned_vehicle(user)
        latest_license = (
            DriverLicense.query.filter_by(driver_id=driver_profile.id if driver_profile else None)
            .order_by(DriverLicense.expiry_date.desc().nulls_last())
            .first()
        )
        documents = (
            DriverDocument.query.filter_by(driver_id=driver_profile.id if driver_profile else None)
            .order_by(DriverDocument.uploaded_at.desc())
            .limit(10)
            .all()
        )
        attendance_summary = self.get_attendance_summary(driver_profile)
        performance = (
            DriverPerformance.query.filter_by(driver_id=driver_profile.id if driver_profile else None)
            .order_by(DriverPerformance.created_at.desc())
            .first()
        )
        incidents = (
            DriverIncident.query.filter_by(driver_id=driver_profile.id if driver_profile else None)
            .order_by(DriverIncident.incident_date.desc())
            .limit(5)
            .all()
        )
        activity_logs = (
            DriverActivityLog.query.filter_by(driver_id=driver_profile.id if driver_profile else None)
            .order_by(DriverActivityLog.created_at.desc())
            .limit(10)
            .all()
        )

        return {
            'user': user,
            'driver_profile': driver_profile,
            'assigned_vehicle': assigned_vehicle,
            'latest_license': latest_license,
            'documents': documents,
            'attendance_summary': attendance_summary,
            'today_attendance': self.get_today_attendance(driver_profile),
            'performance': performance,
            'incidents': incidents,
            'activity_logs': activity_logs,
            'trips': self.get_recent_trips(driver_profile),
            'payroll_record': self.get_latest_payroll(driver_profile),
            'kpi': self.get_driver_kpis(driver_profile, assigned_vehicle),
        }

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

    def get_status_options(self):
        return [
            {'id': 'Active', 'label': 'Active'},
            {'id': 'Inactive', 'label': 'Inactive'},
            {'id': 'Online', 'label': 'Online'},
            {'id': 'Offline', 'label': 'Offline'},
            {'id': 'Suspended', 'label': 'Suspended'},
        ]

    def _get_assigned_vehicle_map(self, users):
        if not users:
            return {}

        usernames = [user.username for user in users if hasattr(user, 'username') and user.username]
        user_ids = [user.id for user in users if hasattr(user, 'id') and user.id]

        vehicles = (
            Vehicle.query.filter(
                or_(Vehicle.assigned_driver.in_(usernames), Vehicle.assigned_driver_id.in_(user_ids))
            )
            .order_by(Vehicle.updated_at.desc())
            .all()
        )
        assignment_map = {}
        for vehicle in vehicles:
            if vehicle.assigned_driver_id and vehicle.assigned_driver_id not in assignment_map:
                assignment_map[vehicle.assigned_driver_id] = vehicle
            elif vehicle.assigned_driver and vehicle.assigned_driver not in assignment_map:
                assignment_map[vehicle.assigned_driver] = vehicle
        return assignment_map

    def find_assigned_vehicle(self, user):
        if not user:
            return None
        query = Vehicle.query
        if user.id:
            query = query.filter(Vehicle.assigned_driver_id == user.id)
        elif user.username:
            query = query.filter(Vehicle.assigned_driver == user.username)
        return query.order_by(Vehicle.updated_at.desc()).first()

    def serialize_driver_row(self, user, assigned_vehicle=None):
        online = self.is_user_online(user)
        status = 'On Duty' if online else 'Offline' if user.is_active else 'Suspended'
        deployment_status = 'Deployed' if assigned_vehicle and assigned_vehicle.current_deployment else 'Ready' if assigned_vehicle else 'Unassigned'

        return {
            'id': user.id,
            'employee_id': user.id[:8].upper(),
            'name': user.username,
            'email': user.email,
            'phone': user.phone or 'N/A',
            'role': user.primary_role.name if user.primary_role else 'Unassigned',
            'driver_code': user.driver_profile.driver_code if hasattr(user, 'driver_profile') and user.driver_profile else 'N/A',
            'assigned_vehicle': assigned_vehicle.vehicle_number if assigned_vehicle else 'Unassigned',
            'attendance_status': 'Checked In' if online else 'Absent',
            'deployment_status': deployment_status,
            'operational_status': status,
            'active': user.is_active,
            'verified': user.is_verified,
            'last_activity': user.last_login_at.isoformat() if user.last_login_at else None,
        }

    def is_user_online(self, user):
        if not user:
            return False
        return (
            user.sessions.filter_by(active=True, revoked=False).count() > 0
        )

    def get_attendance_summary(self, driver_profile):
        if not driver_profile:
            return {'attendance_percentage': 0, 'working_hours': 0, 'late_arrivals': 0, 'weekly_present': 0}

        total_days = driver_profile.attendances.count() or 1
        present_days = driver_profile.attendances.filter(DriverAttendance.status == 'Present').count()
        average_hours = (
            driver_profile.attendances.with_entities(func.avg(DriverAttendance.hours_worked)).scalar() or 0
        )
        late_count = driver_profile.attendances.filter(DriverAttendance.status == 'Late').count()

        return {
            'attendance_percentage': round((present_days / total_days) * 100, 1) if total_days else 0,
            'working_hours': round(average_hours, 1),
            'late_arrivals': late_count,
            'weekly_present': present_days,
        }

    def get_today_attendance(self, driver_profile):
        if not driver_profile:
            return {'status': 'absent', 'check_in': None, 'check_out': None, 'action': 'check_in'}

        attendance = DriverAttendance.query.filter_by(
            driver_id=driver_profile.id,
            date=get_india_today(),
        ).first()

        if not attendance:
            return {'status': 'absent', 'check_in': None, 'check_out': None, 'action': 'check_in'}

        if attendance.check_in and not attendance.check_out:
            return {'status': 'checked_in', 'check_in': attendance.check_in, 'check_out': None, 'action': 'check_out'}

        if attendance.check_in and attendance.check_out:
            return {
                'status': 'checked_out',
                'check_in': attendance.check_in,
                'check_out': attendance.check_out,
                'action': 'none',
            }

        return {'status': 'absent', 'check_in': None, 'check_out': None, 'action': 'check_in'}

    def get_recent_trips(self, driver_profile, limit=5):
        if not driver_profile:
            return []
        return (
            DriverTrip.query.filter_by(driver_id=driver_profile.id)
            .order_by(DriverTrip.trip_date.desc())
            .limit(limit)
            .all()
        )

    def get_latest_payroll(self, driver_profile):
        if not driver_profile:
            return None
        return (
            DriverPayroll.query.filter_by(driver_id=driver_profile.id)
            .order_by(DriverPayroll.payment_date.desc().nulls_last())
            .first()
        )

    def get_driver_kpis(self, driver_profile, assigned_vehicle):
        trips = driver_profile.trips.count() if driver_profile else 0
        import datetime
        first_day_of_month = datetime.date.today().replace(day=1)
        monthly_trips = driver_profile.trips.filter(DriverTrip.trip_date >= first_day_of_month).count() if driver_profile else 0
        violations = driver_profile.incidents.filter(DriverIncident.severity.ilike('%severe%')).count() if driver_profile else 0
        fuel_efficiency = 0
        if driver_profile:
            total_distance = driver_profile.trips.with_entities(func.sum(DriverTrip.distance_km)).scalar() or 0
            total_fuel = driver_profile.trips.with_entities(func.sum(DriverTrip.fuel_consumed_liters)).scalar() or 0
            fuel_efficiency = round((total_distance / total_fuel), 1) if total_fuel else 0

        return {
            'total_trips': trips,
            'monthly_trips': monthly_trips,
            'attendance_percent': self.get_attendance_summary(driver_profile)['attendance_percentage'],
            'safety_score': driver_profile.performance_records.order_by(DriverPerformance.created_at.desc()).with_entities(DriverPerformance.safety_score).scalar() or 0 if driver_profile else 0,
            'rating': driver_profile.performance_records.order_by(DriverPerformance.created_at.desc()).with_entities(DriverPerformance.rating).scalar() or 0 if driver_profile else 0,
            'on_time_percent': driver_profile.performance_records.order_by(DriverPerformance.created_at.desc()).with_entities(DriverPerformance.on_time_percentage).scalar() or 0 if driver_profile else 0,
            'violations': violations,
            'fuel_efficiency': fuel_efficiency,
            'assigned_vehicle_status': assigned_vehicle.status if assigned_vehicle else 'Unassigned',
        }
