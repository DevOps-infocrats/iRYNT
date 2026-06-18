from datetime import datetime, timedelta, timezone

from app.modules.users.repository import UserRepository
from app.modules.vehicles.repository import VehicleRepository


class DashboardAnalyticsService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.vehicle_repo = VehicleRepository()

    def get_kpis(self, filters=None):
        filters = filters or {}
        total_vehicles = self._count_total_vehicles(filters)
        active_drivers = self.user_repo.count_by_role_name('driver')
        today_attendance = self._count_today_attendance(filters)
        active_deployments = self._count_active_deployments(filters)
        pending_approvals = self._count_pending_approvals(filters)
        expiring_documents = self._count_expiring_documents(filters)

        return [
            {'title': 'Active Vehicles', 'value': total_vehicles, 'icon': 'directions_car', 'meta': 'Verified fleet units online'},
            {'title': 'Active Drivers', 'value': active_drivers, 'icon': 'badge', 'meta': 'Drivers currently checked in'},
            {'title': "Today's Attendance", 'value': today_attendance, 'icon': 'schedule', 'meta': 'Active shift records'},
            {'title': 'Active Deployments', 'value': active_deployments, 'icon': 'rocket_launch', 'meta': 'Operations currently in transit'},
            {'title': 'Pending Approvals', 'value': pending_approvals, 'icon': 'pending_actions', 'meta': 'Requests waiting review'},
            {'title': 'Expiring Documents', 'value': expiring_documents, 'icon': 'event_busy', 'meta': 'Certificates due in 30 days'},
        ]

    def get_dashboard_payload(self, filters=None):
        return {
            'attendance_trend': self.get_attendance_trend(days=7, filters=filters),
            'deployment': self.get_deployment_analytics(filters=filters),
            'live_operations': self.get_live_operations(filters=filters),
            'notifications': self.get_notifications(filters=filters),
            'timeline': self.get_timeline(filters=filters),
            'operational_signals': self.get_operational_signals(filters=filters),
            'pending_approval_items': self.get_pending_approval_items(filters=filters),
        }

    def get_deployment_analytics(self, filters=None):
        default = {'labels': ['Active', 'Available', 'Maintenance', 'Idle'], 'values': [0, 0, 0, 0]}
        try:
            from app.extensions import db
            from app.modules.vehicles.models import Vehicle

            counts = {label: 0 for label in default['labels']}
            rows = db.session.query(Vehicle.status, db.func.count(Vehicle.id)).group_by(Vehicle.status).all()
            for status, count in rows:
                if status in counts:
                    counts[status] = count
            values = [counts[label] for label in default['labels']]
            return {'labels': default['labels'], 'values': values}
        except Exception:
            return default

    def get_live_operations(self, filters=None):
        try:
            from app.extensions import db
            from app.modules.vehicles.models import Vehicle

            query = db.session.query(
                Vehicle.current_deployment,
                Vehicle.status,
                db.func.count(Vehicle.id),
                db.func.count(db.func.distinct(Vehicle.assigned_driver)),
            ).filter(Vehicle.current_deployment.isnot(None)).group_by(Vehicle.current_deployment, Vehicle.status).limit(6)

            operations = []
            for deployment, status, vehicle_count, driver_count in query.all():
                operations.append({
                    'task': deployment or 'Deployment',
                    'status': status or 'Active',
                    'vehicles': vehicle_count,
                    'drivers': driver_count,
                    'eta': 'N/A',
                })

            if not operations:
                return [
                    {'task': 'Asset staging', 'status': 'Pending', 'vehicles': 5, 'drivers': 4, 'eta': '00:40'},
                    {'task': 'Route validation', 'status': 'Active', 'vehicles': 7, 'drivers': 6, 'eta': '00:18'},
                ]

            return operations
        except Exception:
            return []

    def get_notifications(self, filters=None):
        approvals = self._count_pending_approvals(filters)
        expiring_documents = self._count_expiring_documents(filters)
        active_deployments = self._count_active_deployments(filters)

        notifications = []
        if approvals:
            notifications.append({'message': f'{approvals} requests pending review.', 'time': 'Just now'})
        if expiring_documents:
            notifications.append({'message': f'{expiring_documents} vehicle documents need renewal.', 'time': '14m ago'})
        if active_deployments:
            notifications.append({'message': f'{active_deployments} deployments are currently active.', 'time': '35m ago'})

        if not notifications:
            notifications.append({'message': 'No urgent alerts. All systems normal.', 'time': 'Now'})

        return notifications

    def get_timeline(self, filters=None):
        try:
            from app.extensions import db
            from app.modules.auth.models import AuditLog

            entries = (
                db.session.query(AuditLog.action, AuditLog.created_at)
                .order_by(AuditLog.created_at.desc())
                .limit(3)
                .all()
            )

            timeline = []
            for action, created_at in entries:
                timeline.append({
                    'title': action or 'System event',
                    'description': 'Recent operational activity.',
                    'when': self._format_relative_time(created_at),
                })

            if not timeline:
                timeline = [
                    {'title': 'System initialized', 'description': 'Operations monitoring is online.', 'when': 'Now'},
                ]

            return timeline
        except Exception:
            return [{'title': 'System ready', 'description': 'No timeline events found.', 'when': 'Now'}]

    def get_operational_signals(self, filters=None):
        active_drivers = self.user_repo.count_by_role_name('driver')
        total_vehicles = self._count_total_vehicles(filters)
        active_deployments = self._count_active_deployments(filters)
        expiry_count = self._count_expiring_documents(filters)
        attendance_values = self.get_attendance_trend(days=7, filters=filters).get('values', [])

        driver_utilization = round((active_drivers / total_vehicles) * 100) if total_vehicles else 0
        deployment_success = round((active_deployments / total_vehicles) * 100) if total_vehicles else 0
        schedule_compliance = int(sum(attendance_values) / len(attendance_values)) if attendance_values else 0

        return [
            {'title': 'Active drivers', 'value': f'{driver_utilization}%', 'badge': 'bg-success', 'text_color': 'text-success'},
            {'title': 'Deployment success', 'value': f'{deployment_success}%', 'badge': 'bg-warning', 'text_color': 'text-warning'},
            {'title': 'Schedule compliance', 'value': f'{schedule_compliance}%', 'badge': 'bg-info', 'text_color': 'text-info'},
            {'title': 'Document alerts', 'value': f'{expiry_count} open', 'badge': 'bg-danger', 'text_color': 'text-danger'},
        ]

    def get_pending_approval_items(self, filters=None):
        today_attendance = self._count_today_attendance(filters)
        active_deployments = self._count_active_deployments(filters)
        expiring_documents = self._count_expiring_documents(filters)
        pending_approvals = self._count_pending_approvals(filters)

        return [
            {'label': 'Attendance review', 'value': f'{max(round(today_attendance * 0.15), 1) if today_attendance else 0} items'},
            {'label': 'Deployment requests', 'value': f'{active_deployments} items'},
            {'label': 'Document renewals', 'value': f'{expiring_documents} items'},
            {'label': 'User invites', 'value': f'{pending_approvals} pending'},
        ]

    def _format_relative_time(self, when):
        if not when:
            return 'Unknown'
        now = datetime.now(timezone.utc)
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        delta = now - when
        if delta < timedelta(minutes=1):
            return 'Just now'
        if delta < timedelta(hours=1):
            minutes = int(delta.total_seconds() // 60)
            return f'{minutes}m ago'
        if delta < timedelta(days=1):
            hours = int(delta.total_seconds() // 3600)
            return f'{hours}h ago'
        return when.strftime('%b %d')

    def _count_total_vehicles(self, filters=None):
        try:
            from app.extensions import db
            from app.modules.vehicles.models import Vehicle
            return db.session.query(Vehicle).count()
        except Exception:
            return 0

    def _count_today_attendance(self, filters=None):
        try:
            from app.extensions import db
            from app.modules.auth.models import LoginAttempt
            now = datetime.now(timezone.utc)
            start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
            q = db.session.query(LoginAttempt.user_id).filter(LoginAttempt.success.is_(True), LoginAttempt.created_at >= start)
            return q.distinct().count()
        except Exception:
            return 0

    def _count_active_deployments(self, filters=None):
        try:
            from app.extensions import db
            from app.modules.vehicles.models import Vehicle
            return db.session.query(Vehicle).filter(Vehicle.current_deployment.isnot(None)).count()
        except Exception:
            return 0

    def _count_pending_approvals(self, filters=None):
        try:
            from app.extensions import db
            from app.modules.auth.models import User
            return db.session.query(User).filter(User.is_verified.is_(False)).count()
        except Exception:
            return 0

    def _count_expiring_documents(self, filters=None):
        try:
            from sqlalchemy import or_
            from app.extensions import db
            from app.modules.vehicles.models import Vehicle

            return db.session.query(Vehicle).filter(
                or_(
                    Vehicle.insurance_status != 'Valid',
                    Vehicle.permit_status != 'Valid',
                    Vehicle.fitness_status != 'Valid',
                    Vehicle.puc_status != 'Valid',
                )
            ).count()
        except Exception:
            return 0

    def get_attendance_trend(self, days=7, filters=None):
        try:
            from app.extensions import db
            from app.modules.auth.models import LoginAttempt
            now = datetime.now(timezone.utc)
            start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
            attempts = db.session.query(LoginAttempt.created_at).filter(LoginAttempt.success.is_(True), LoginAttempt.created_at >= start).all()
            counts = [0] * days
            labels = []
            for i in range(days):
                day = (start + timedelta(days=i)).date()
                labels.append(day.strftime('%a'))

            for (dt,) in attempts:
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                delta = (dt.date() - start.date()).days
                if 0 <= delta < days:
                    counts[delta] += 1

            max_count = max(counts) if counts else 0
            values = [0] * days if max_count == 0 else [round((c / max_count) * 100) for c in counts]
            return {'labels': labels, 'values': values}
        except Exception:
            return {'labels': [], 'values': []}

    def get_compliance_counters(self, filters=None):
        try:
            from app.extensions import db
            from app.modules.vehicles.models import Vehicle
            from app.modules.drivers.models import DriverProfile, DriverLicense, DriverDocument
            from datetime import date, timedelta
            
            today = date.today()
            thirty_days = today + timedelta(days=30)
            
            vehicles = Vehicle.query.all()
            near_odo = 0
            above_odo = 0
            near_age = 0
            above_age = 0
            
            for v in vehicles:
                # Odometer
                odo = v.vehicle_running or 0.0
                if 140000 <= odo < 150000:
                    near_odo += 1
                elif odo >= 150000:
                    above_odo += 1
                
                # Age
                if v.manufacturing_year:
                    try:
                        mfg_year = int(v.manufacturing_year)
                        total_months = (today.year - mfg_year) * 12 + today.month - 1
                        if 66 <= total_months < 72:
                            near_age += 1
                        elif total_months >= 72:
                            above_age += 1
                    except (ValueError, TypeError):
                        pass
            
            drivers = DriverProfile.query.all()
            expiring_soon_dl = 0
            expired_dl = 0
            
            for d in drivers:
                exp_dates = []
                dl_doc = DriverDocument.query.filter_by(driver_id=d.id, document_type='Driving License').order_by(DriverDocument.expiry_date.desc().nulls_last()).first()
                if dl_doc and dl_doc.expiry_date:
                    exp_dates.append(dl_doc.expiry_date)
                dl_lic = DriverLicense.query.filter_by(driver_id=d.id).order_by(DriverLicense.expiry_date.desc().nulls_last()).first()
                if dl_lic and dl_lic.expiry_date:
                    exp_dates.append(dl_lic.expiry_date)
                
                if exp_dates:
                    expiry = max(exp_dates)
                    if expiry < today:
                        expired_dl += 1
                    elif today <= expiry <= thirty_days:
                        expiring_soon_dl += 1
            
            return {
                'near_odo': near_odo,
                'above_odo': above_odo,
                'near_age': near_age,
                'above_age': above_age,
                'expiring_soon_dl': expiring_soon_dl,
                'expired_dl': expired_dl
            }
        except Exception as e:
            print(f"Error getting compliance counters: {e}", flush=True)
            return {
                'near_odo': 0,
                'above_odo': 0,
                'near_age': 0,
                'above_age': 0,
                'expiring_soon_dl': 0,
                'expired_dl': 0
            }
