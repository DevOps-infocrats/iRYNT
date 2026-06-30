from datetime import datetime, timedelta

from sqlalchemy.orm import joinedload

from app.extensions import db
from app.modules.attendance.approval_constants import (
    APPROVAL_STATUS_KAM_APPROVED,
    APPROVAL_STATUS_MIS_APPROVED,
    APPROVAL_STATUS_REJECTED,
    APPROVAL_STATUS_SUBMITTED,
)
from app.modules.attendance.utils import get_india_now
from app.modules.approvals.models import ApprovalHistory, ApprovalRequest
from app.modules.auth.models import Role, User
from app.modules.deployments.models import VehicleDeployment
from app.modules.drivers.models import DriverAttendance, DriverProfile
from app.modules.notifications.helpers import create_notification_safe
from app.domain.auth.policies.auth_policy import has_role


class AttendanceApprovalService:
    WORKFLOW_APPROVAL_TYPE = 'attendance_verification'
    WORKFLOW_HIERARCHY_SCOPE = 'attendance_mis_kam'
    OPEN_WORKFLOW_STATUSES = ('Pending', 'Under Review', 'Escalated')

    def _resolve_scope_fields(self, attendance, driver_profile):
        circle_id = self.resolve_attendance_circle_id(attendance)
        company_id = driver_profile.user.company_id if driver_profile.user else None
        client_id = driver_profile.client_id
        project_id = driver_profile.project_id
        subzone_id = driver_profile.subzone_id

        if driver_profile.user_id:
            deployment = (
                VehicleDeployment.query.filter_by(
                    driver_id=driver_profile.user_id,
                    status='Active',
                    approval_status='Approved',
                )
                .order_by(VehicleDeployment.actual_start.desc())
                .first()
            )
            if deployment and deployment.project:
                company_id = deployment.project.company_id or company_id
                circle_id = deployment.project.circle_id or circle_id
                client_id = deployment.project.client_id or client_id
                project_id = deployment.project_id or project_id
                subzone_id = deployment.subzone_id or subzone_id

        return {
            'company_id': company_id,
            'circle_id': circle_id,
            'client_id': client_id,
            'project_id': project_id,
            'subzone_id': subzone_id,
        }

    def _find_circle_user_by_role(self, circle_id, role_names):
        if not circle_id:
            return None
        return (
            User.query.join(User.roles)
            .filter(Role.name.in_(role_names), User.circle_id == circle_id)
            .order_by(User.username.asc())
            .first()
        )

    def _get_open_workflow_request(self, attendance):
        return (
            ApprovalRequest.query.filter_by(
                entity_type='driver_attendance',
                entity_id=attendance.id,
                approval_type=self.WORKFLOW_APPROVAL_TYPE,
                hierarchy_scope=self.WORKFLOW_HIERARCHY_SCOPE,
            )
            .filter(ApprovalRequest.approval_status.in_(self.OPEN_WORKFLOW_STATUSES))
            .order_by(ApprovalRequest.submitted_at.desc())
            .first()
        )

    def _get_workflow_request(self, attendance):
        return (
            ApprovalRequest.query.filter_by(
                entity_type='driver_attendance',
                entity_id=attendance.id,
                approval_type=self.WORKFLOW_APPROVAL_TYPE,
                hierarchy_scope=self.WORKFLOW_HIERARCHY_SCOPE,
            )
            .order_by(ApprovalRequest.submitted_at.desc())
            .first()
        )

    def _add_workflow_history(self, approval_id, action, user_id, old_status, new_status, remarks=None):
        db.session.add(
            ApprovalHistory(
                approval_request_id=approval_id,
                action_taken=action,
                action_by_id=user_id,
                previous_status=old_status,
                new_status=new_status,
                remarks=remarks,
            )
        )

    def sync_workflow_on_submission(self, attendance, driver_profile, requested_by_id):
        if self._get_open_workflow_request(attendance):
            return None

        scope = self._resolve_scope_fields(attendance, driver_profile)
        mis_user = self._find_circle_user_by_role(scope['circle_id'], ['MIS', 'Circle Admin'])
        employee_name = driver_profile.user.username if driver_profile.user else 'Employee'
        role_label = 'Helper' if self.is_helper_attendance(attendance) else 'Driver'

        approval = ApprovalRequest(
            approval_type=self.WORKFLOW_APPROVAL_TYPE,
            module_name='attendance',
            entity_type='driver_attendance',
            entity_id=attendance.id,
            request_title=f'Attendance verification - {employee_name}',
            request_description=(
                f'{role_label} attendance for {attendance.date} submitted for Circle MIS → KAM approval.'
            ),
            requested_by_id=requested_by_id or driver_profile.user_id,
            assigned_approver_id=mis_user.id if mis_user else None,
            hierarchy_scope=self.WORKFLOW_HIERARCHY_SCOPE,
            company_id=scope.get('company_id'),
            circle_id=scope.get('circle_id'),
            client_id=scope.get('client_id'),
            project_id=scope.get('project_id'),
            subzone_id=scope.get('subzone_id'),
            priority='Medium',
            approval_status='Pending',
            sla_due_at=get_india_now() + timedelta(hours=8),
            remarks='Auto-created for Circle MIS verification.',
        )
        db.session.add(approval)
        db.session.flush()
        self._add_workflow_history(
            approval.id,
            'CREATED',
            requested_by_id or driver_profile.user_id,
            None,
            'Pending',
            'Attendance submitted — awaiting Circle MIS verification.',
        )
        return approval

    def sync_workflow_mis_approved(self, attendance, user, remarks=None):
        request = self._get_open_workflow_request(attendance)
        if not request:
            return

        old_status = request.approval_status
        kam_user = self._find_circle_user_by_role(request.circle_id, ['Circle KAM'])
        request.approval_status = 'Under Review'
        request.assigned_approver_id = kam_user.id if kam_user else None
        if remarks:
            request.remarks = remarks
        request.updated_at = datetime.utcnow()
        self._add_workflow_history(
            request.id,
            'MIS_APPROVED',
            user.id,
            old_status,
            'Under Review',
            remarks or 'MIS verification complete — awaiting Circle KAM approval.',
        )

    def sync_workflow_kam_approved(self, attendance, user, remarks=None):
        request = self._get_open_workflow_request(attendance) or self._get_workflow_request(attendance)
        if not request or request.approval_status == 'Approved':
            return

        old_status = request.approval_status
        request.approval_status = 'Approved'
        request.approved_at = datetime.utcnow()
        request.assigned_approver_id = user.id
        if remarks:
            request.remarks = remarks
        request.updated_at = datetime.utcnow()
        self._add_workflow_history(
            request.id,
            'KAM_APPROVED',
            user.id,
            old_status,
            'Approved',
            remarks or 'Final Circle KAM approval granted.',
        )

        profile = attendance.driver
        if profile and profile.user_id:
            att_date = attendance.date.strftime('%Y-%m-%d') if attendance.date else 'today'
            create_notification_safe(
                user_id=profile.user_id,
                message=f'Attendance Approved: Your attendance for {att_date} has been fully approved.',
                module='attendance',
                priority='High',
                related_type='attendance',
                related_id=str(attendance.id),
                route='/attendance/live',
            )

    def sync_workflow_rejected(self, attendance, user, remarks=None, stage='MIS'):
        request = self._get_open_workflow_request(attendance) or self._get_workflow_request(attendance)
        if not request or request.approval_status in ('Approved', 'Rejected'):
            return

        old_status = request.approval_status
        request.approval_status = 'Rejected'
        request.rejected_at = datetime.utcnow()
        request.remarks = remarks
        request.updated_at = datetime.utcnow()
        self._add_workflow_history(
            request.id,
            f'{stage}_REJECTED',
            user.id,
            old_status,
            'Rejected',
            remarks,
        )

    def resolve_attendance_circle_id(self, attendance):
        profile = attendance.driver
        if not profile:
            return None
        if profile.circle_id:
            return profile.circle_id
        if profile.user and profile.user.circle_id:
            return profile.user.circle_id
        if profile.user_id:
            deployment = (
                VehicleDeployment.query.filter_by(
                    driver_id=profile.user_id,
                    status='Active',
                    approval_status='Approved',
                )
                .order_by(VehicleDeployment.actual_start.desc())
                .first()
            )
            if deployment and deployment.project:
                return deployment.project.circle_id
        return None

    def is_helper_attendance(self, attendance):
        profile = attendance.driver
        return bool(profile and profile.user and has_role(profile.user, 'Helper'))

    def user_can_access_attendance(self, user, attendance):
        if not user:
            return False
        if user.is_superadmin:
            return True
        circle_id = self.resolve_attendance_circle_id(attendance)
        if not circle_id or not user.circle_id:
            return False
        return user.circle_id == circle_id

    def user_is_mis(self, user):
        return has_role(user, 'MIS') or has_role(user, 'Circle Admin')

    def user_is_circle_kam(self, user):
        return has_role(user, 'Circle KAM')

    def list_mis_pending(self, user, page=1, per_page=20):
        records = (
            DriverAttendance.query.options(
                joinedload(DriverAttendance.driver).joinedload(DriverProfile.user),
            )
            .filter(
                DriverAttendance.approval_status == APPROVAL_STATUS_SUBMITTED,
                DriverAttendance.check_in.isnot(None),
            )
            .order_by(DriverAttendance.check_in.desc())
            .all()
        )
        if user and not user.is_superadmin:
            records = [r for r in records if self.user_can_access_attendance(user, r)]
        total = len(records)
        start = (page - 1) * per_page
        return records[start:start + per_page], total

    def list_kam_pending(self, user, page=1, per_page=20):
        records = (
            DriverAttendance.query.options(
                joinedload(DriverAttendance.driver).joinedload(DriverProfile.user),
            )
            .filter(
                DriverAttendance.approval_status == APPROVAL_STATUS_MIS_APPROVED,
                DriverAttendance.check_in.isnot(None),
            )
            .order_by(DriverAttendance.mis_verified_at.desc().nullslast())
            .all()
        )
        if user and not user.is_superadmin:
            records = [r for r in records if self.user_can_access_attendance(user, r)]
        total = len(records)
        start = (page - 1) * per_page
        return records[start:start + per_page], total

    def initialize_submission(self, attendance):
        attendance.approval_status = APPROVAL_STATUS_SUBMITTED
        attendance.seatbelt_verified = False
        attendance.selfie_verified = False
        attendance.dashboard_verified = False
        attendance.odometer_verified = False
        attendance.helmet_verified = False
        attendance.safety_shoes_verified = False
        attendance.safety_jacket_verified = False
        attendance.id_card_verified = False
        attendance.mis_verified_by = None
        attendance.mis_verified_at = None
        attendance.mis_remarks = None
        attendance.kam_verified_by = None
        attendance.kam_verified_at = None
        attendance.kam_remarks = None

    def reset_for_resubmission(self, attendance, user, remarks=None):
        attendance.check_in = None
        attendance.check_out = None
        attendance.hours_worked = None
        attendance.approval_status = APPROVAL_STATUS_REJECTED
        attendance.mis_verified_by = user.id
        attendance.mis_verified_at = datetime.utcnow()
        attendance.mis_remarks = f'[RESUBMISSION REQUESTED] {remarks or ""}'.strip()
        for field in (
            'seatbelt_verified', 'selfie_verified', 'dashboard_verified', 'odometer_verified',
            'helmet_verified', 'safety_shoes_verified', 'safety_jacket_verified', 'id_card_verified',
        ):
            setattr(attendance, field, False)
        attendance.kam_verified_by = None
        attendance.kam_verified_at = None
        attendance.kam_remarks = None

    def notify_mis_users(self, attendance, driver_profile):
        circle_id = self.resolve_attendance_circle_id(attendance)
        try:
            mis_users = (
                User.query.join(User.roles)
                .filter(Role.name.in_(['MIS', 'Circle Admin']))
                .filter(User.circle_id == circle_id)
                .all()
            )
            employee_name = driver_profile.user.username if driver_profile.user else 'Employee'
            for mis_user in mis_users:
                create_notification_safe(
                    user_id=mis_user.id,
                    message=f'Attendance submitted by {employee_name} — pending MIS verification.',
                    module='attendance',
                    priority='Medium',
                    related_type='attendance',
                    related_id=str(attendance.id),
                    route='/attendance/mis-approvals',
                    company_id=driver_profile.user.company_id if driver_profile.user else None,
                    circle_id=circle_id,
                )
        except Exception:
            pass

    def notify_kam_users(self, attendance, driver_profile):
        circle_id = self.resolve_attendance_circle_id(attendance)
        try:
            kam_users = (
                User.query.join(User.roles)
                .filter(Role.name == 'Circle KAM')
                .filter(User.circle_id == circle_id)
                .all()
            )
            employee_name = driver_profile.user.username if driver_profile.user else 'Employee'
            for kam_user in kam_users:
                create_notification_safe(
                    user_id=kam_user.id,
                    message=f'Attendance for {employee_name} MIS-approved — pending KAM approval.',
                    module='attendance',
                    priority='Medium',
                    related_type='attendance',
                    related_id=str(attendance.id),
                    route='/attendance/kam-approvals',
                    company_id=driver_profile.user.company_id if driver_profile.user else None,
                    circle_id=circle_id,
                )
        except Exception:
            pass

    def mis_approve(self, attendance, user, checklist, remarks=None):
        if attendance.approval_status != APPROVAL_STATUS_SUBMITTED:
            return None, 'Attendance is not pending MIS approval.'
        if not self.user_is_mis(user):
            return None, 'Only Circle MIS users can perform this action.'
        if not self.user_can_access_attendance(user, attendance):
            return None, 'Cross-circle approval is not allowed.'

        is_helper = self.is_helper_attendance(attendance)
        if is_helper:
            attendance.helmet_verified = bool(checklist.get('helmet_verified'))
            attendance.safety_shoes_verified = bool(checklist.get('safety_shoes_verified'))
            attendance.safety_jacket_verified = bool(checklist.get('safety_jacket_verified'))
            attendance.id_card_verified = bool(checklist.get('id_card_verified'))
        else:
            attendance.seatbelt_verified = bool(checklist.get('seatbelt_verified'))
            attendance.selfie_verified = bool(checklist.get('selfie_verified'))
            attendance.dashboard_verified = bool(checklist.get('dashboard_verified'))
            attendance.odometer_verified = bool(checklist.get('odometer_verified'))

        attendance.approval_status = APPROVAL_STATUS_MIS_APPROVED
        attendance.mis_verified_by = user.id
        attendance.mis_verified_at = datetime.utcnow()
        attendance.mis_remarks = remarks
        self.sync_workflow_mis_approved(attendance, user, remarks)
        db.session.commit()
        self.notify_kam_users(attendance, attendance.driver)
        return attendance, None

    def mis_reject(self, attendance, user, remarks=None):
        if attendance.approval_status != APPROVAL_STATUS_SUBMITTED:
            return None, 'Attendance is not pending MIS approval.'
        if not self.user_is_mis(user):
            return None, 'Only Circle MIS users can perform this action.'
        if not self.user_can_access_attendance(user, attendance):
            return None, 'Cross-circle approval is not allowed.'

        attendance.approval_status = APPROVAL_STATUS_REJECTED
        attendance.mis_verified_by = user.id
        attendance.mis_verified_at = datetime.utcnow()
        attendance.mis_remarks = remarks
        self.sync_workflow_rejected(attendance, user, remarks, stage='MIS')
        db.session.commit()
        return attendance, None

    def mis_request_resubmission(self, attendance, user, remarks=None):
        if attendance.approval_status != APPROVAL_STATUS_SUBMITTED:
            return None, 'Attendance is not pending MIS approval.'
        if not self.user_is_mis(user):
            return None, 'Only Circle MIS users can perform this action.'
        if not self.user_can_access_attendance(user, attendance):
            return None, 'Cross-circle approval is not allowed.'

        self.reset_for_resubmission(attendance, user, remarks)
        self.sync_workflow_rejected(
            attendance,
            user,
            attendance.mis_remarks,
            stage='MIS_RESUBMISSION',
        )
        db.session.commit()
        return attendance, None

    def kam_approve(self, attendance, user, remarks=None):
        if attendance.approval_status != APPROVAL_STATUS_MIS_APPROVED:
            return None, 'Attendance is not pending KAM approval.'
        if not self.user_is_circle_kam(user):
            return None, 'Only Circle KAM users can perform this action.'
        if not self.user_can_access_attendance(user, attendance):
            return None, 'Cross-circle approval is not allowed.'

        attendance.approval_status = APPROVAL_STATUS_KAM_APPROVED
        attendance.kam_verified_by = user.id
        attendance.kam_verified_at = datetime.utcnow()
        attendance.kam_remarks = remarks
        self.sync_workflow_kam_approved(attendance, user, remarks)
        db.session.commit()
        return attendance, None

    def kam_reject(self, attendance, user, remarks=None):
        if attendance.approval_status != APPROVAL_STATUS_MIS_APPROVED:
            return None, 'Attendance is not pending KAM approval.'
        if not self.user_is_circle_kam(user):
            return None, 'Only Circle KAM users can perform this action.'
        if not self.user_can_access_attendance(user, attendance):
            return None, 'Cross-circle approval is not allowed.'

        attendance.approval_status = APPROVAL_STATUS_REJECTED
        attendance.kam_verified_by = user.id
        attendance.kam_verified_at = datetime.utcnow()
        attendance.kam_remarks = remarks
        self.sync_workflow_rejected(attendance, user, remarks, stage='KAM')
        db.session.commit()
        return attendance, None

    def get_attendance_context(self, attendance):
        profile = attendance.driver
        user = profile.user if profile else None
        deployment = None
        vehicle = None
        project = profile.project if profile else None
        circle = profile.circle if profile else None

        if user:
            deployment = (
                VehicleDeployment.query.filter_by(
                    driver_id=user.id,
                    status='Active',
                    approval_status='Approved',
                )
                .order_by(VehicleDeployment.actual_start.desc())
                .first()
            )
            if deployment:
                vehicle = deployment.vehicle
                if deployment.project:
                    project = deployment.project
                    circle = deployment.project.circle

        mis_verifier = User.query.get(attendance.mis_verified_by) if attendance.mis_verified_by else None

        return {
            'attendance': attendance,
            'profile': profile,
            'user': user,
            'deployment': deployment,
            'vehicle': vehicle,
            'project': project,
            'circle': circle,
            'is_helper': self.is_helper_attendance(attendance),
            'mis_verifier': mis_verifier,
        }
