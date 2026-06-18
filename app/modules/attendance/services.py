from datetime import date

from app.extensions import db
from app.modules.approvals.models import ApprovalRequest
from app.modules.attendance.repository import AttendanceRepository
from app.modules.attendance.utils import get_india_now, get_india_today
from app.modules.drivers.models import DriverAttendance, DriverProfile
from app.services.geolocation.attendance_geo_service import AttendanceGeoService
from app.modules.notifications.helpers import create_notification_safe


class FallbackHelperAssignment:
    def __init__(self, circle, project, subzone, shift='Day'):
        self.circle = circle
        self.project = project
        self.subzone = subzone
        self.shift = shift


class AttendanceService:
    def __init__(self):
        self.repository = AttendanceRepository()
        self.geo_service = AttendanceGeoService()

    def list_live_attendance(self, filters, page, per_page):
        return self.repository.list_live_attendance(filters, page, per_page)

    def list_attendance_history(self, filters, page, per_page):
        return self.repository.list_attendance_history(filters, page, per_page)

    def get_monitoring_summary(self, filters):
        return self.repository.get_monitoring_summary(filters)

    def get_attendance_approvals(self):
        return (
            ApprovalRequest.query.filter_by(
                module_name='attendance',
                entity_type='driver_attendance',
            )
            .filter(ApprovalRequest.approval_status.in_(['Pending', 'Under Review', 'Escalated']))
            .order_by(ApprovalRequest.submitted_at.desc())
            .all()
        )

    def get_shift_reports(self):
        # Placeholder for future attendance reporting integration.
        return {}

    def mark_attendance(self, driver_profile_id, action, location_payload=None, actor_id=None, selfie_path=None, dashboard_path=None, odometer=None):
        driver_profile = DriverProfile.query.get(driver_profile_id)
        if not driver_profile:
            return None, 'Driver profile could not be found.'

        if driver_profile.user:
            from app.modules.users.services import ensure_helper_profile
            ensure_helper_profile(driver_profile.user)
            driver_profile = DriverProfile.query.get(driver_profile_id)

        location_payload = location_payload or {}
        geo_result, geo_error = self.geo_service.validate_attendance_location(driver_profile, location_payload)
        if geo_error:
            return None, geo_error

        from app.domain.auth.policies.auth_policy import has_role
        is_helper = has_role(driver_profile.user, 'Helper') if (driver_profile and driver_profile.user) else False
        
        active_helper_assignment = None
        if is_helper:
            from app.modules.deployments.models import HelperAssignment
            active_helper_assignment = HelperAssignment.query.filter_by(
                helper_id=driver_profile.user_id,
                status='Active'
            ).first()
            if not active_helper_assignment:
                from app.modules.deployments.models import VehicleDeployment
                active_dep = VehicleDeployment.query.filter(
                    VehicleDeployment.driver_id == driver_profile.user_id,
                    VehicleDeployment.status == 'Active',
                    VehicleDeployment.approval_status == 'Approved'
                ).first()
                if active_dep:
                    active_helper_assignment = FallbackHelperAssignment(
                        circle=active_dep.project.circle if (active_dep.project and hasattr(active_dep.project, 'circle')) else None,
                        project=active_dep.project,
                        subzone=active_dep.subzone,
                        shift='Day'
                    )
                elif driver_profile.circle_id and driver_profile.project_id and driver_profile.subzone_id:
                    from app.modules.circles.models import Circle
                    from app.modules.projects.models import Project
                    from app.modules.subzones.models import Subzone
                    circle = Circle.query.get(driver_profile.circle_id)
                    project = Project.query.get(driver_profile.project_id)
                    subzone = Subzone.query.get(driver_profile.subzone_id)
                    active_helper_assignment = FallbackHelperAssignment(
                        circle=circle,
                        project=project,
                        subzone=subzone,
                        shift='Day'
                    )

        today = get_india_today()
        attendance = DriverAttendance.query.filter_by(driver_id=driver_profile.id, date=today).first()

        if action == 'check_in':
            if attendance and attendance.check_in:
                return attendance, 'Driver is already checked in for today.'

            if not attendance:
                attendance = DriverAttendance(
                    driver_id=driver_profile.id,
                    date=today,
                    shift_name=active_helper_assignment.shift if (is_helper and active_helper_assignment) else None,
                    status='Present',
                )
                db.session.add(attendance)

            attendance.check_in = get_india_now()
            attendance.status = 'Present'
            if selfie_path:
                attendance.selfie_storage_path = selfie_path
            if dashboard_path:
                attendance.dashboard_storage_path = dashboard_path
            if odometer is not None:
                attendance.start_odometer = odometer
            self._process_attendance_odometer(attendance, driver_profile, odometer)

            self.geo_service.apply_geo_result(attendance, action, location_payload, geo_result)
            db.session.flush()
            self.geo_service.create_review_request_if_needed(
                attendance,
                driver_profile,
                geo_result,
                action,
                actor_id or driver_profile.user_id,
            )
            # Safe notification for assigned approver (if geo review created)
            try:
                from app.modules.approvals.models import ApprovalRequest
                pending = ApprovalRequest.query.filter_by(entity_type='driver_attendance', entity_id=attendance.id).filter(ApprovalRequest.approval_status.in_(['Pending', 'Under Review', 'Escalated'])).first()
                if pending and pending.assigned_approver_id:
                    create_notification_safe(
                        user_id=pending.assigned_approver_id,
                        message=f"Attendance requires review for {driver_profile.user.username if driver_profile.user else 'Driver'}",
                        module='attendance',
                        priority='High',
                        related_type='attendance',
                        related_id=str(attendance.id),
                        route=f"/attendance/approvals",
                        metadata={'attendance_id': attendance.id},
                        company_id=pending.company_id,
                        circle_id=pending.circle_id
                    )
            except Exception:
                pass
            self.geo_service.log_geo_audit(attendance, driver_profile, geo_result, action, actor_id)
            self._trigger_attendance_notifications(attendance, driver_profile, geo_result, action)
            db.session.commit()
            return attendance, None

        if action == 'check_out':
            if not attendance or not attendance.check_in:
                return None, 'Cannot check out before checking in.'
            if attendance.check_out:
                return attendance, 'Driver has already checked out today.'

            attendance.check_out = get_india_now()
            check_in_naive = attendance.check_in.replace(tzinfo=None) if attendance.check_in.tzinfo else attendance.check_in
            check_out_naive = attendance.check_out.replace(tzinfo=None) if attendance.check_out.tzinfo else attendance.check_out
            attendance.hours_worked = round(
                (check_out_naive - check_in_naive).total_seconds() / 3600.0,
                2,
            )
            attendance.status = 'Present'
            if attendance.hours_worked < 0:
                attendance.hours_worked = 0

            if selfie_path:
                attendance.selfie_storage_path = selfie_path
            if dashboard_path:
                attendance.dashboard_storage_path = dashboard_path
            if odometer is not None:
                attendance.end_odometer = odometer
            self._process_attendance_odometer(attendance, driver_profile, odometer)

            self.geo_service.apply_geo_result(attendance, action, location_payload, geo_result)
            db.session.flush()
            self.geo_service.create_review_request_if_needed(
                attendance,
                driver_profile,
                geo_result,
                action,
                actor_id or driver_profile.user_id,
            )
            # Safe notification for assigned approver (if geo review created)
            try:
                from app.modules.approvals.models import ApprovalRequest
                pending = ApprovalRequest.query.filter_by(entity_type='driver_attendance', entity_id=attendance.id).filter(ApprovalRequest.approval_status.in_(['Pending', 'Under Review', 'Escalated'])).first()
                if pending and pending.assigned_approver_id:
                    create_notification_safe(
                        user_id=pending.assigned_approver_id,
                        message=f"Attendance requires review for {driver_profile.user.username if driver_profile.user else 'Driver'}",
                        module='attendance',
                        priority='High',
                        related_type='attendance',
                        related_id=str(attendance.id),
                        route=f"/attendance/approvals",
                        metadata={'attendance_id': attendance.id},
                        company_id=pending.company_id,
                        circle_id=pending.circle_id
                    )
            except Exception:
                pass
            self.geo_service.log_geo_audit(attendance, driver_profile, geo_result, action, actor_id)
            self._trigger_attendance_notifications(attendance, driver_profile, geo_result, action)
            db.session.commit()
            return attendance, None

        return None, 'Unsupported attendance action.'

    def _process_attendance_odometer(self, attendance, driver_profile, odometer):
        if odometer is None:
            return
        try:
            from app.modules.deployments.models import VehicleDeployment
            from app.modules.vehicles.models import Vehicle
            from app.modules.notifications.helpers import create_notification_safe
            
            # Fetch active deployment for this driver
            deployment = (
                VehicleDeployment.query.filter(
                    VehicleDeployment.driver_id == driver_profile.user_id,
                    VehicleDeployment.status == 'Active',
                    VehicleDeployment.approval_status == 'Approved',
                )
                .order_by(VehicleDeployment.actual_start.desc(), VehicleDeployment.created_at.desc())
                .first()
            )
            if not deployment or not deployment.vehicle_id:
                return
                
            vehicle = Vehicle.query.get(deployment.vehicle_id)
            if not vehicle:
                return
                
            previous_km = vehicle.vehicle_running or 0.0
            new_km = float(odometer)
            driver_circle_id = driver_profile.circle_id or (driver_profile.user.circle_id if driver_profile.user else None)
            
            if new_km < previous_km:
                # Flag attendance and notify
                attendance.verification_status = 'Requires Verification'
                msg = f"KM Anomaly: Vehicle {vehicle.vehicle_number} odometer decreased from {previous_km} to {new_km}."
                
                from app.modules.auth.models import User, Role
                from sqlalchemy.orm import joinedload
                admins = User.query.join(User.roles).filter(Role.name.in_(['Circle Admin', 'Super Admin'])).options(joinedload(User.roles)).all()
                for admin in admins:
                    is_circle_admin = any(r.name == 'Circle Admin' for r in admin.roles)
                    if is_circle_admin and admin.circle_id and admin.circle_id != driver_circle_id:
                        continue
                    create_notification_safe(
                        user_id=admin.id,
                        message=msg,
                        module='vehicles',
                        priority='Critical',
                        related_type='vehicle',
                        related_id=vehicle.id,
                        metadata={'vehicle_number': vehicle.vehicle_number, 'previous_km': previous_km, 'new_km': new_km}
                    )
            else:
                # Update vehicle running odometer
                vehicle.vehicle_running = new_km
                db.session.add(vehicle)
                
                # Check thresholds
                if new_km >= 150000:
                    msg = f"150000 KM Restriction: Vehicle {vehicle.vehicle_number} has reached {new_km} KM. Deployment restricted."
                    from app.modules.auth.models import User, Role
                    from sqlalchemy.orm import joinedload
                    admins = User.query.join(User.roles).filter(Role.name.in_(['Circle Admin', 'Super Admin'])).options(joinedload(User.roles)).all()
                    for admin in admins:
                        is_circle_admin = any(r.name == 'Circle Admin' for r in admin.roles)
                        if is_circle_admin and admin.circle_id and admin.circle_id != driver_circle_id:
                            continue
                        create_notification_safe(
                            user_id=admin.id,
                            message=msg,
                            module='vehicles',
                            priority='Critical',
                            related_type='vehicle',
                            related_id=vehicle.id
                        )
                elif new_km >= 140000:
                    msg = f"140000 KM Warning: Vehicle {vehicle.vehicle_number} has reached {new_km} KM. Maintenance required soon."
                    from app.modules.auth.models import User, Role
                    from sqlalchemy.orm import joinedload
                    admins = User.query.join(User.roles).filter(Role.name.in_(['Circle Admin', 'Super Admin'])).options(joinedload(User.roles)).all()
                    for admin in admins:
                        is_circle_admin = any(r.name == 'Circle Admin' for r in admin.roles)
                        if is_circle_admin and admin.circle_id and admin.circle_id != driver_circle_id:
                            continue
                        create_notification_safe(
                            user_id=admin.id,
                            message=msg,
                            module='vehicles',
                            priority='Warning',
                            related_type='vehicle',
                            related_id=vehicle.id
                        )
        except Exception:
            pass

    def _trigger_attendance_notifications(self, attendance, driver_profile, geo_result, action):
        from app.modules.notifications.helpers import create_notification_safe
        
        deployment = geo_result.get('deployment') if geo_result else None
        target_company_id = driver_profile.user.company_id if driver_profile.user else None
        target_circle_id = driver_profile.circle_id or (driver_profile.user.circle_id if driver_profile.user else None)
        if deployment and deployment.project:
            target_company_id = deployment.project.company_id
            target_circle_id = deployment.project.circle_id

        # 1. Send 'Attendance Marked' notification to the user themselves
        try:
            check_time = get_india_now().strftime('%H:%M:%S')
            action_label = "checked in" if action == 'check_in' else "checked out"
            create_notification_safe(
                user_id=driver_profile.user_id,
                message=f"Attendance Marked: You {action_label} successfully at {check_time}.",
                module='attendance',
                priority='Medium',
                related_type='attendance',
                related_id=str(attendance.id),
                route='/attendance/live',
                company_id=target_company_id,
                circle_id=target_circle_id
            )
        except Exception:
            pass

        # 2. Check if geo status is OUTSIDE_GEOFENCE
        if geo_result and geo_result.get('geo_status') == 'OUTSIDE_GEOFENCE':
            # Set verification_status of attendance to 'Requires Review'
            attendance.verification_status = 'Requires Review'
            db.session.add(attendance)
            db.session.flush()

            # Notify user about Outside Geofence
            try:
                create_notification_safe(
                    user_id=driver_profile.user_id,
                    message=f"Attendance Outside Geofence: Your attendance check-in/out was marked outside the assigned geofence.",
                    module='attendance',
                    priority='High',
                    related_type='attendance',
                    related_id=str(attendance.id),
                    route='/attendance/live',
                    company_id=target_company_id,
                    circle_id=target_circle_id
                )
            except Exception:
                pass

            # Notify Circle KAM roles in the same circle
            try:
                from app.modules.auth.models import User, Role
                from sqlalchemy.orm import joinedload
                
                # Query Circle KAM users
                kams = User.query.join(User.roles).filter(Role.name == 'Circle KAM').options(joinedload(User.roles)).all()
                
                notified = False
                for kam in kams:
                    if kam.circle_id and kam.circle_id != target_circle_id:
                        continue
                    create_notification_safe(
                        user_id=kam.id,
                        message=f"Attendance Outside Geofence: {driver_profile.user.username if driver_profile.user else 'Helper'} marked attendance outside the geofence.",
                        module='attendance',
                        priority='High',
                        related_type='attendance',
                        related_id=str(attendance.id),
                        route='/attendance/approvals',
                        metadata={'attendance_id': attendance.id, 'driver_id': driver_profile.id},
                        company_id=target_company_id,
                        circle_id=target_circle_id
                    )
                    notified = True
                
                if not notified:
                    # Fallback to circle-scoped system-wide notification
                    create_notification_safe(
                        user_id=None,
                        message=f"Attendance Outside Geofence: {driver_profile.user.username if driver_profile.user else 'Helper'} marked attendance outside the geofence.",
                        module='attendance',
                        priority='High',
                        related_type='attendance',
                        related_id=str(attendance.id),
                        route='/attendance/approvals',
                        metadata={'attendance_id': attendance.id, 'driver_id': driver_profile.id},
                        company_id=target_company_id,
                        circle_id=target_circle_id
                    )
            except Exception:
                pass
