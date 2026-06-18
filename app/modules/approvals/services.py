"""
Approval Service

Business logic for approval workflows.
Handles approval creation, assignment, approval/rejection, escalation.
"""

from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.modules.approvals.repository import ApprovalRepository
from app.modules.approvals.models import ApprovalRequest, ApprovalStatus, ApprovalPriority
from app.modules.notifications.helpers import create_notification_safe


class ApprovalService:
    """Service for approval operations"""

    def __init__(self):
        self.repository = ApprovalRepository()

    def create_approval(self, payload):
        """Create approval request"""
        approval = self.repository.create_approval(payload)
        
        # Add history entry
        self.repository.add_history(
            approval.id,
            'CREATED',
            payload.get('created_by_id'),
            None,
            'Pending',
            'Approval request created'
        )
        # Safe notification: notify assigned approver if available
        try:
            assigned = approval.assigned_approver_id
            if assigned:
                create_notification_safe(
                    user_id=assigned,
                    message=f"Approval request: {approval.request_title}",
                    module='approvals',
                    priority='High',
                    related_type='approval',
                    related_id=str(approval.id),
                    route=f"/pending-approvals/view/{approval.id}",
                    metadata={'approval_id': approval.id}
                )
        except Exception:
            pass

        return approval

    def assign_approver(self, approval_id, approver_id, assigned_by_id):
        """Assign approver to approval"""
        approval = self.repository.get_approval(approval_id)
        if not approval:
            return None, 'Approval not found'

        old_approver = approval.assigned_approver_id
        approval.assigned_approver_id = approver_id
        approval.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        # Add history
        self.repository.add_history(
            approval_id,
            'REASSIGNED',
            assigned_by_id,
            f'Assigned to {old_approver}' if old_approver else None,
            'Pending',
            f'Reassigned to new approver'
        )
        return approval, None

    def approve_approval(self, approval_id, approver_id, remarks=None):
        """Approve an approval request"""
        approval = self.repository.get_approval(approval_id)
        if not approval:
            return None, 'Approval not found'

        if approval.approval_status not in ['Pending', 'Under Review', 'Escalated']:
            return None, f'Cannot approve {approval.approval_status} request'

        old_status = approval.approval_status
        approval.approval_status = 'Approved'
        approval.approved_at = datetime.now(timezone.utc)
        approval.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        # Trigger notification & update attendance verification_status
        try:
            if approval.entity_type == 'driver_attendance':
                from app.modules.drivers.models import DriverAttendance
                att = DriverAttendance.query.get(approval.entity_id)
                if att:
                    att.verification_status = 'Approved'
                    db.session.add(att)
                    db.session.commit()
                att_date = att.date.strftime('%Y-%m-%d') if (att and att.date) else 'today'
                create_notification_safe(
                    user_id=approval.requested_by_id,
                    message=f"Attendance Approved: Your attendance for {att_date} has been approved.",
                    module='attendance',
                    priority='High',
                    related_type='attendance',
                    related_id=str(approval.entity_id),
                    route='/attendance/live'
                )
        except Exception:
            pass

        # Add history
        self.repository.add_history(
            approval_id,
            'APPROVED',
            approver_id,
            old_status,
            'Approved',
            remarks
        )
        return approval, None

    def reject_approval(self, approval_id, approver_id, remarks=None):
        """Reject an approval request"""
        approval = self.repository.get_approval(approval_id)
        if not approval:
            return None, 'Approval not found'

        if approval.approval_status not in ['Pending', 'Under Review', 'Escalated']:
            return None, f'Cannot reject {approval.approval_status} request'

        old_status = approval.approval_status
        approval.approval_status = 'Rejected'
        approval.rejected_at = datetime.now(timezone.utc)
        approval.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        # Trigger notification & update attendance verification_status
        try:
            if approval.entity_type == 'driver_attendance':
                from app.modules.drivers.models import DriverAttendance
                att = DriverAttendance.query.get(approval.entity_id)
                if att:
                    att.verification_status = 'Rejected'
                    db.session.add(att)
                    db.session.commit()
                att_date = att.date.strftime('%Y-%m-%d') if (att and att.date) else 'today'
                create_notification_safe(
                    user_id=approval.requested_by_id,
                    message=f"Attendance Rejected: Your attendance for {att_date} has been rejected.",
                    module='attendance',
                    priority='High',
                    related_type='attendance',
                    related_id=str(approval.entity_id),
                    route='/attendance/live'
                )
        except Exception:
            pass

        # Add history
        self.repository.add_history(
            approval_id,
            'REJECTED',
            approver_id,
            old_status,
            'Rejected',
            remarks
        )
        return approval, None

    def escalate_approval(self, approval_id, escalated_by_id, remarks=None):
        """Escalate approval to higher level"""
        approval = self.repository.get_approval(approval_id)
        if not approval:
            return None, 'Approval not found'

        old_status = approval.approval_status
        approval.approval_status = 'Escalated'
        approval.escalated_at = datetime.now(timezone.utc)
        approval.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        # Add history
        self.repository.add_history(
            approval_id,
            'ESCALATED',
            escalated_by_id,
            old_status,
            'Escalated',
            remarks or 'Escalated due to SLA or priority'
        )
        # Safe notifications: inform requester and assigned approver (if any)
        try:
            if approval.requested_by_id:
                create_notification_safe(
                    user_id=approval.requested_by_id,
                    message=f"Your approval request '{approval.request_title}' was escalated.",
                    module='approvals',
                    priority='High',
                    related_type='approval',
                    related_id=str(approval.id),
                    route=f"/pending-approvals/view/{approval.id}",
                    metadata={'approval_id': approval.id}
                )
            if approval.assigned_approver_id:
                create_notification_safe(
                    user_id=approval.assigned_approver_id,
                    message=f"Approval request '{approval.request_title}' has been escalated.",
                    module='approvals',
                    priority='High',
                    related_type='approval',
                    related_id=str(approval.id),
                    route=f"/pending-approvals/view/{approval.id}",
                    metadata={'approval_id': approval.id}
                )
        except Exception:
            pass
        return approval, None

    def update_status(self, approval_id, new_status, updated_by_id, remarks=None):
        """Update approval status"""
        approval = self.repository.get_approval(approval_id)
        if not approval:
            return None, 'Approval not found'

        old_status = approval.approval_status
        approval.approval_status = new_status
        approval.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        # Add history
        self.repository.add_history(
            approval_id,
            'STATUS_CHANGED',
            updated_by_id,
            old_status,
            new_status,
            remarks
        )
        return approval, None

    def add_comment(self, approval_id, user_id, comment):
        """Add comment to approval"""
        return self.repository.add_comment(approval_id, user_id, comment)

    def get_approval(self, approval_id):
        """Get approval details"""
        return self.repository.get_approval(approval_id)

    def list_approvals(self, filters=None, offset=0, limit=20, sort_by='submitted_at', sort_order='desc', user=None):
        """List approvals"""
        return self.repository.list_approvals(filters, offset, limit, sort_by, sort_order, user=user)

    def get_pending_approvals(self, offset=0, limit=20):
        """Get pending approvals"""
        return self.repository.get_pending_approvals(offset, limit)

    def get_approvals_for_approver(self, approver_id, offset=0, limit=20):
        """Get approvals for approver"""
        return self.repository.get_approvals_for_approver(approver_id, offset, limit)

    def get_escalated_approvals(self, offset=0, limit=20):
        """Get escalated approvals"""
        return self.repository.get_escalated_approvals(offset, limit)

    def get_sla_breached_approvals(self):
        """Get SLA breached approvals"""
        return self.repository.get_sla_breached_approvals()

    def get_approval_history(self, approval_id):
        """Get approval history"""
        return self.repository.get_approval_history(approval_id)

    def get_approval_comments(self, approval_id):
        """Get approval comments"""
        return self.repository.get_approval_comments(approval_id)

    def get_approval_stats(self, filters=None, user=None):
        """Get approval statistics"""
        return self.repository.get_approval_stats(filters, user=user)

    def bulk_approve(self, approval_ids, approver_id, remarks=None):
        """Bulk approve multiple approvals"""
        results = []
        for approval_id in approval_ids:
            result = self.approve_approval(approval_id, approver_id, remarks)
            results.append(result)
        return results

    def bulk_reject(self, approval_ids, approver_id, remarks=None):
        """Bulk reject multiple approvals"""
        results = []
        for approval_id in approval_ids:
            result = self.reject_approval(approval_id, approver_id, remarks)
            results.append(result)
        return results

    def bulk_escalate(self, approval_ids, escalated_by_id, remarks=None):
        """Bulk escalate multiple approvals"""
        results = []
        for approval_id in approval_ids:
            result = self.escalate_approval(approval_id, escalated_by_id, remarks)
            results.append(result)
        return results

    def get_dashboard_metrics(self, user=None, company_id=None, user_id=None):
        """Get approval dashboard metrics"""
        if not user and user_id:
            from app.modules.auth.models import User
            user = User.query.get(user_id)

        filters = {}
        if company_id:
            filters['company_id'] = company_id

        stats = self.repository.get_approval_stats(filters, user=user)

        return {
            'total_pending': stats['pending'],
            'critical_pending': stats['critical_pending'],
            'sla_breached': stats['sla_breached'],
            'awaiting_approval': stats['under_review'],
            'approved_today': stats['approved_today'],
            'escalated': stats['escalated'],
            'my_pending': stats['my_pending'],
            'total_stats': stats,
        }
