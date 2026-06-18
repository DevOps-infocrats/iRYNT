from datetime import date, datetime

from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.modules.attendance.utils import get_india_today
from app.modules.auth.models import Role, User
from app.modules.drivers.models import DriverAttendance, DriverProfile


class AttendanceRepository:
    def _driver_role_query(self):
        return (
            User.query.options(joinedload(User.driver_profile))
            .filter(
                or_(
                    User.primary_role.has(Role.name.ilike('driver')),
                    User.primary_role.has(Role.name.ilike('helper')),
                    User.roles.any(Role.name.ilike('driver')),
                    User.roles.any(Role.name.ilike('helper')),
                )
            )
            .filter(User.driver_profile != None)
        )

    def _apply_filters(self, query, filters):
        if not filters:
            return query

        # Filter by specific driver profile (for driver-only view)
        if filters.get('driver_id'):
            query = query.join(User.driver_profile).filter(DriverProfile.id == filters['driver_id'])

        company_id = filters.get('company_id')
        circle_id = filters.get('circle_id')

        if company_id or circle_id:
            from app.modules.deployments.models import VehicleDeployment
            from app.modules.projects.models import Project
            
            query = query.outerjoin(
                VehicleDeployment,
                (VehicleDeployment.driver_id == User.id) & (VehicleDeployment.status == 'Active')
            ).outerjoin(
                Project,
                Project.id == VehicleDeployment.project_id
            )
            
            if company_id:
                query = query.filter(
                    or_(
                        User.company_id == company_id,
                        Project.company_id == company_id
                    )
                )
            if circle_id:
                query = query.filter(
                    or_(
                        User.circle_id == circle_id,
                        Project.circle_id == circle_id
                    )
                )

        if filters.get('search_query'):
            search_value = f"%{filters['search_query']}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_value),
                    User.email.ilike(search_value),
                    User.phone.ilike(search_value),
                    User.id.ilike(search_value),
                    User.driver_profile.has(DriverProfile.driver_code.ilike(search_value)),
                )
            )

        return query

    def list_live_attendance(self, filters, page, per_page):
        query = self._apply_filters(self._driver_role_query(), filters)
        total = query.distinct().count()
        offset = (page - 1) * per_page
        drivers = query.order_by(User.username).offset(offset).limit(per_page).all()

        today = get_india_today()
        attendances = DriverAttendance.query.filter_by(date=today).all()
        attendance_map = {attendance.driver_id: attendance for attendance in attendances}

        rows = []
        for user in drivers:
            profile = user.driver_profile
            attendance = attendance_map.get(profile.id) if profile else None
            if attendance and attendance.check_out:
                current_status = 'Completed'
            elif attendance and attendance.check_in:
                current_status = 'Present'
            else:
                current_status = 'Absent'

            rows.append(
                {
                    'id': user.id,
                    'name': user.username,
                    'email': user.email,
                    'driver_code': profile.driver_code if profile else None,
                    'driver_profile_id': profile.id if profile else None,
                    'today_status': current_status,
                    'check_in': attendance.check_in if attendance else None,
                    'check_out': attendance.check_out if attendance else None,
                    'hours_worked': attendance.hours_worked if attendance else None,
                    'geo_verified': attendance.geo_verified if attendance else None,
                    'geo_status': attendance.geo_status if attendance else None,
                    'geo_distance_meters': attendance.geo_distance_meters if attendance else None,
                    'location_accuracy': attendance.location_accuracy if attendance else None,
                    'subzone_name': profile.subzone.subzone_name if profile and profile.subzone else None,
                    'allowed_radius': (
                        (profile.subzone.attendance_radius or profile.subzone.allowed_radius)
                        if profile and profile.subzone else None
                    ),
                    'attendance_id': attendance.id if attendance else None,
                    'selfie_storage_path': attendance.selfie_storage_path if attendance else None,
                    'dashboard_storage_path': attendance.dashboard_storage_path if attendance else None,
                    'start_odometer': attendance.start_odometer if attendance else None,
                    'end_odometer': attendance.end_odometer if attendance else None,
                }
            )

        return rows, total

    def list_attendance_history(self, filters, page, per_page):
        query = (
            DriverAttendance.query.options(joinedload(DriverAttendance.driver).joinedload(DriverProfile.user))
        )

        # Filter by specific driver profile (for driver-only view)
        if filters.get('driver_id'):
            query = query.filter(DriverAttendance.driver_id == filters['driver_id'])

        if filters.get('search_query'):
            search_value = f"%{filters['search_query']}%"
            query = query.join(DriverAttendance.driver).join(DriverProfile.user).filter(
                or_(
                    User.username.ilike(search_value),
                    User.email.ilike(search_value),
                    DriverProfile.driver_code.ilike(search_value),
                )
            )

        if filters.get('date_from'):
            try:
                query = query.filter(DriverAttendance.date >= datetime.strptime(filters['date_from'], '%Y-%m-%d').date())
            except ValueError:
                pass

        if filters.get('date_to'):
            try:
                query = query.filter(DriverAttendance.date <= datetime.strptime(filters['date_to'], '%Y-%m-%d').date())
            except ValueError:
                pass

        total = query.count()
        offset = (page - 1) * per_page
        records = query.order_by(DriverAttendance.date.desc(), DriverAttendance.check_in.desc()).offset(offset).limit(per_page).all()

        return records, total

    def get_monitoring_summary(self, filters):
        driver_query = self._apply_filters(self._driver_role_query(), filters)
        total_drivers = driver_query.distinct().count()

        today = get_india_today()
        checked_in = DriverAttendance.query.filter(DriverAttendance.date == today, DriverAttendance.check_in.isnot(None)).count()
        checked_out = DriverAttendance.query.filter(DriverAttendance.date == today, DriverAttendance.check_out.isnot(None)).count()
        geo_verified = DriverAttendance.query.filter(
            DriverAttendance.date == today,
            DriverAttendance.geo_status == 'GEO_VERIFIED',
        ).count()
        outside_geofence = DriverAttendance.query.filter(
            DriverAttendance.date == today,
            DriverAttendance.geo_status == 'OUTSIDE_GEOFENCE',
        ).count()
        low_accuracy = DriverAttendance.query.filter(
            DriverAttendance.date == today,
            DriverAttendance.geo_status == 'LOW_ACCURACY',
        ).count()
        pending_checkins = max(total_drivers - checked_in, 0)
        coverage = int((checked_in / total_drivers) * 100) if total_drivers else 0

        return {
            'total_drivers': total_drivers,
            'checked_in': checked_in,
            'checked_out': checked_out,
            'geo_verified': geo_verified,
            'outside_geofence': outside_geofence,
            'low_accuracy': low_accuracy,
            'pending_checkins': pending_checkins,
            'coverage_percent': coverage,
        }
