"""
Approval Repository

Data access layer for approval operations.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import or_, and_

from app.extensions import db
from app.modules.approvals.models import ApprovalRequest, ApprovalWorkflow, ApprovalHistory, ApprovalComment


class ApprovalRepository:
    """Repository for approval data access"""

    def get_approval(self, approval_id):
        """Get approval by ID"""
        return ApprovalRequest.query.filter_by(id=approval_id).first()

    def list_approvals(self, filters=None, offset=0, limit=20, sort_by='submitted_at', sort_order='desc', user=None):
        """List approvals with filters"""
        filters = filters or {}
        query = ApprovalRequest.query

        # Apply filters
        if filters.get('approval_status'):
            query = query.filter_by(approval_status=filters['approval_status'])
        if filters.get('approval_type'):
            query = query.filter_by(approval_type=filters['approval_type'])
        if filters.get('approval_types'):
            query = query.filter(ApprovalRequest.approval_type.in_(filters['approval_types']))
        if filters.get('is_overdue'):
            now = datetime.now(timezone.utc)
            query = query.filter(
                ApprovalRequest.sla_due_at < now,
                ApprovalRequest.approval_status.in_(['Pending', 'Under Review', 'Escalated'])
            )
        if filters.get('priority'):
            query = query.filter_by(priority=filters['priority'])
        if filters.get('assigned_approver_id'):
            query = query.filter_by(assigned_approver_id=filters['assigned_approver_id'])
        if filters.get('company_id'):
            query = query.filter_by(company_id=filters['company_id'])
        if filters.get('circle_id'):
            query = query.filter_by(circle_id=filters['circle_id'])
        if filters.get('client_id'):
            query = query.filter_by(client_id=filters['client_id'])
        if filters.get('project_id'):
            query = query.filter_by(project_id=filters['project_id'])
        if filters.get('subzone_id'):
            query = query.filter_by(subzone_id=filters['subzone_id'])

        # Role-based query filtering
        if user and not user.is_superadmin:
            role_conditions = [
                or_(
                    ApprovalRequest.assigned_approver_id == user.id,
                    ApprovalRequest.requested_by_id == user.id
                )
            ]
            
            # 1. Driver / Helper: own requests
            if 'driver' in user.role_names or 'helper' in user.role_names:
                role_conditions.append(ApprovalRequest.requested_by_id == user.id)
                
            # 2. Circle KAM / Circle Admin
            if 'circle kam' in user.role_names or 'circle admin' in user.role_names:
                allowed_types = [
                    'attendance_correction', 'leave_approval', 'overtime_approval', 'payroll_verification',
                    'driver_verification', 'license_verification', 'compliance_approval', 'medical_certificate',
                    'vehicle_document', 'insurance_verification', 'vehicle_assignment',
                    'escalation_closure', 'sla_override', 'critical_incident', 'escalation_reassignment'
                ]
                role_conditions.append(
                    and_(
                        ApprovalRequest.circle_id == user.circle_id,
                        ApprovalRequest.approval_type.in_(allowed_types)
                    )
                )
                
            # 3. PMO
            if 'pmo' in user.role_names:
                allowed_types = ['project_approval', 'subzone_approval', 'sla_override']
                role_conditions.append(ApprovalRequest.approval_type.in_(allowed_types))
                
            # 4. Corporate KAM / Corporate Admin / CBH / Key Account Manager
            if any(r in user.role_names for r in ['corporate admin', 'corporate kam', 'cbh', 'key account manager', 'corporate customer']):
                if user.company_id:
                    role_conditions.append(ApprovalRequest.company_id == user.company_id)
                else:
                    role_conditions.append(db.literal(True))
                    
            query = query.filter(or_(*role_conditions))

        # Search
        if filters.get('search_query'):
            search = f"%{filters['search_query']}%"
            query = query.filter(
                or_(
                    ApprovalRequest.request_title.ilike(search),
                    ApprovalRequest.request_description.ilike(search),
                )
            )

        # Sort
        if sort_by == 'submitted_at':
            query = query.order_by(ApprovalRequest.submitted_at.desc() if sort_order == 'desc' else ApprovalRequest.submitted_at.asc())
        elif sort_by == 'sla_due_at':
            query = query.order_by(ApprovalRequest.sla_due_at.asc() if sort_order == 'asc' else ApprovalRequest.sla_due_at.desc())
        elif sort_by == 'priority':
            query = query.order_by(ApprovalRequest.priority.desc() if sort_order == 'desc' else ApprovalRequest.priority.asc())

        total = query.count()
        approvals = query.offset(offset).limit(limit).all()
        return approvals, total

    def create_approval(self, payload):
        """Create new approval request"""
        approval = ApprovalRequest(**payload)
        db.session.add(approval)
        db.session.commit()
        return approval

    def update_approval(self, approval_id, payload):
        """Update approval"""
        approval = self.get_approval(approval_id)
        if not approval:
            return None
        for key, value in payload.items():
            setattr(approval, key, value)
        db.session.commit()
        return approval

    def get_pending_approvals(self, offset=0, limit=20):
        """Get pending approvals"""
        query = ApprovalRequest.query.filter_by(approval_status='Pending').order_by(ApprovalRequest.submitted_at.desc())
        total = query.count()
        approvals = query.offset(offset).limit(limit).all()
        return approvals, total

    def get_approvals_for_approver(self, approver_id, offset=0, limit=20):
        """Get approvals assigned to specific approver"""
        query = ApprovalRequest.query.filter(
            ApprovalRequest.assigned_approver_id == approver_id,
            ApprovalRequest.approval_status.in_(['Pending', 'Under Review', 'Escalated'])
        ).order_by(ApprovalRequest.sla_due_at.asc())
        total = query.count()
        approvals = query.offset(offset).limit(limit).all()
        return approvals, total

    def get_sla_breached_approvals(self):
        """Get approvals with breached SLA"""
        now = datetime.now(timezone.utc)
        query = ApprovalRequest.query.filter(
            ApprovalRequest.sla_due_at < now,
            ApprovalRequest.approval_status.in_(['Pending', 'Under Review'])
        ).order_by(ApprovalRequest.sla_due_at.asc())
        return query.all()

    def get_escalated_approvals(self, offset=0, limit=20):
        """Get escalated approvals"""
        query = ApprovalRequest.query.filter_by(approval_status='Escalated').order_by(ApprovalRequest.escalated_at.desc())
        total = query.count()
        approvals = query.offset(offset).limit(limit).all()
        return approvals, total

    def add_history(self, approval_id, action_taken, action_by_id, previous_status, new_status, remarks=None):
        """Add approval history entry"""
        history = ApprovalHistory(
            approval_request_id=approval_id,
            action_taken=action_taken,
            action_by_id=action_by_id,
            previous_status=previous_status,
            new_status=new_status,
            remarks=remarks,
        )
        db.session.add(history)
        db.session.commit()
        return history

    def get_approval_history(self, approval_id):
        """Get approval history"""
        return ApprovalHistory.query.filter_by(approval_request_id=approval_id).order_by(ApprovalHistory.action_time.desc()).all()

    def add_comment(self, approval_id, user_id, comment):
        """Add comment to approval"""
        comment_obj = ApprovalComment(
            approval_request_id=approval_id,
            user_id=user_id,
            comment=comment,
        )
        db.session.add(comment_obj)
        db.session.commit()
        return comment_obj

    def get_approval_comments(self, approval_id):
        """Get approval comments"""
        return ApprovalComment.query.filter_by(approval_request_id=approval_id).order_by(ApprovalComment.created_at.desc()).all()

    def get_workflow_levels(self, approval_type):
        """Get approval workflow levels"""
        return ApprovalWorkflow.query.filter_by(approval_type=approval_type, active=True).order_by(ApprovalWorkflow.approval_level.asc()).all()

    def get_approval_stats(self, filters=None, user=None):
        """Get approval statistics"""
        filters = filters or {}
        query = ApprovalRequest.query

        # Apply basic filters
        if filters.get('company_id'):
            query = query.filter_by(company_id=filters['company_id'])
        if filters.get('assigned_approver_id'):
            query = query.filter_by(assigned_approver_id=filters['assigned_approver_id'])

        # Apply role-based filters
        if user and not user.is_superadmin:
            role_conditions = [
                or_(
                    ApprovalRequest.assigned_approver_id == user.id,
                    ApprovalRequest.requested_by_id == user.id
                )
            ]
            
            # 1. Driver / Helper
            if 'driver' in user.role_names or 'helper' in user.role_names:
                role_conditions.append(ApprovalRequest.requested_by_id == user.id)
                
            # 2. Circle KAM / Circle Admin
            if 'circle kam' in user.role_names or 'circle admin' in user.role_names:
                allowed_types = [
                    'attendance_correction', 'leave_approval', 'overtime_approval', 'payroll_verification',
                    'driver_verification', 'license_verification', 'compliance_approval', 'medical_certificate',
                    'vehicle_document', 'insurance_verification', 'vehicle_assignment',
                    'escalation_closure', 'sla_override', 'critical_incident', 'escalation_reassignment'
                ]
                role_conditions.append(
                    and_(
                        ApprovalRequest.circle_id == user.circle_id,
                        ApprovalRequest.approval_type.in_(allowed_types)
                    )
                )
                
            # 3. PMO
            if 'pmo' in user.role_names:
                allowed_types = ['project_approval', 'subzone_approval', 'sla_override']
                role_conditions.append(ApprovalRequest.approval_type.in_(allowed_types))
                
            # 4. Corporate KAM / Corporate Admin / CBH / Key Account Manager
            if any(r in user.role_names for r in ['corporate admin', 'corporate kam', 'cbh', 'key account manager', 'corporate customer']):
                if user.company_id:
                    role_conditions.append(ApprovalRequest.company_id == user.company_id)
                else:
                    role_conditions.append(db.literal(True))
                    
            query = query.filter(or_(*role_conditions))

        total = query.count()
        pending = query.filter(ApprovalRequest.approval_status == 'Pending').count()
        under_review = query.filter(ApprovalRequest.approval_status == 'Under Review').count()
        escalated = query.filter(ApprovalRequest.approval_status == 'Escalated').count()
        approved = query.filter(ApprovalRequest.approval_status == 'Approved').count()
        rejected = query.filter(ApprovalRequest.approval_status == 'Rejected').count()
        critical_pending = query.filter(ApprovalRequest.approval_status == 'Pending', ApprovalRequest.priority == 'Critical').count()
        
        # SLA breached
        now = datetime.now(timezone.utc)
        sla_breached = query.filter(
            ApprovalRequest.sla_due_at < now,
            ApprovalRequest.approval_status.in_(['Pending', 'Under Review'])
        ).count()
        
        # Approved today
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        approved_today = query.filter(
            ApprovalRequest.approval_status == 'Approved',
            ApprovalRequest.approved_at >= today_start
        ).count()

        # My pending actions (assigned to the current user and pending/under review/escalated)
        my_pending = query.filter(
            ApprovalRequest.assigned_approver_id == user.id if user else db.literal(False),
            ApprovalRequest.approval_status.in_(['Pending', 'Under Review', 'Escalated'])
        ).count() if user else 0

        return {
            'total': total,
            'pending': pending,
            'under_review': under_review,
            'escalated': escalated,
            'approved': approved,
            'rejected': rejected,
            'critical_pending': critical_pending,
            'sla_breached': sla_breached,
            'approved_today': approved_today,
            'my_pending': my_pending,
        }
