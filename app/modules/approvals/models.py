"""
Approval Models

Enterprise-grade approval workflow ORM models.
Supports multi-level approvals, SLA tracking, hierarchy-aware filtering.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from app.extensions import db


def make_uuid():
    return str(uuid.uuid4())


class ApprovalType(Enum):
    """Approval categories"""
    # Workforce Approvals
    EMPLOYEE_ONBOARDING = 'employee_onboarding'
    DRIVER_VERIFICATION = 'driver_verification'
    LABOUR_APPROVAL = 'labour_approval'
    FRT_ASSIGNMENT = 'frt_assignment'
    USER_ACTIVATION = 'user_activation'
    
    # Document Approvals
    LICENSE_VERIFICATION = 'license_verification'
    INSURANCE_VERIFICATION = 'insurance_verification'
    COMPLIANCE_APPROVAL = 'compliance_approval'
    MEDICAL_CERTIFICATE = 'medical_certificate'
    VEHICLE_DOCUMENT = 'vehicle_document'
    
    # Operational Approvals
    PROJECT_APPROVAL = 'project_approval'
    SUBZONE_APPROVAL = 'subzone_approval'
    FRT_ACTIVATION = 'frt_activation'
    VEHICLE_ASSIGNMENT = 'vehicle_assignment'
    
    # Escalation Approvals
    ESCALATION_CLOSURE = 'escalation_closure'
    SLA_OVERRIDE = 'sla_override'
    CRITICAL_INCIDENT = 'critical_incident'
    ESCALATION_REASSIGNMENT = 'escalation_reassignment'
    
    # Attendance & Payroll
    ATTENDANCE_CORRECTION = 'attendance_correction'
    LEAVE_APPROVAL = 'leave_approval'
    OVERTIME_APPROVAL = 'overtime_approval'
    PAYROLL_VERIFICATION = 'payroll_verification'


class ApprovalStatus(Enum):
    """Approval request status"""
    PENDING = 'Pending'
    UNDER_REVIEW = 'Under Review'
    ESCALATED = 'Escalated'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'
    EXPIRED = 'Expired'


class ApprovalPriority(Enum):
    """Request priority levels"""
    LOW = 'Low'
    MEDIUM = 'Medium'
    HIGH = 'High'
    CRITICAL = 'Critical'


class ApprovalRequest(db.Model):
    """
    Centralized approval request model.
    Stores all pending approval requests across enterprise.
    """
    __tablename__ = 'approval_requests'
    __table_args__ = (
        db.Index('idx_approval_requests_approval_type', 'approval_type'),
        db.Index('idx_approval_requests_approval_status', 'approval_status'),
        db.Index('idx_approval_requests_assigned_approver', 'assigned_approver_id'),
        db.Index('idx_approval_requests_requested_by', 'requested_by_id'),
        db.Index('idx_approval_requests_company_id', 'company_id'),
        db.Index('idx_approval_requests_circle_id', 'circle_id'),
        db.Index('idx_approval_requests_client_id', 'client_id'),
        db.Index('idx_approval_requests_project_id', 'project_id'),
        db.Index('idx_approval_requests_subzone_id', 'subzone_id'),
        db.Index('idx_approval_requests_sla_due_at', 'sla_due_at'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    
    # Approval Identity
    approval_type = db.Column(db.String(50), nullable=False, index=True)
    module_name = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(100), nullable=False)
    entity_id = db.Column(db.String(36), nullable=False)
    
    # Request Details
    request_title = db.Column(db.String(255), nullable=False)
    request_description = db.Column(db.Text, nullable=True)
    
    # Requester & Approver
    requested_by_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    assigned_approver_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Hierarchy Scope
    hierarchy_scope = db.Column(db.String(100), nullable=True)
    company_id = db.Column(db.String(36), nullable=True, index=True)
    circle_id = db.Column(db.String(36), nullable=True, index=True)
    client_id = db.Column(db.String(36), nullable=True, index=True)
    project_id = db.Column(db.String(36), nullable=True, index=True)
    subzone_id = db.Column(db.String(36), nullable=True, index=True)
    frt_id = db.Column(db.String(36), nullable=True, index=True)
    
    # Priority & Status
    priority = db.Column(db.String(20), default='Medium', nullable=False)
    approval_status = db.Column(db.String(20), default='Pending', nullable=False, index=True)
    
    # Timestamps & SLA
    sla_due_at = db.Column(db.DateTime(timezone=True), nullable=True, index=True)
    submitted_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    rejected_at = db.Column(db.DateTime(timezone=True), nullable=True)
    escalated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Additional Info
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    requested_by = db.relationship('User', foreign_keys=[requested_by_id], lazy='joined')
    assigned_approver = db.relationship('User', foreign_keys=[assigned_approver_id], lazy='joined')
    history = db.relationship('ApprovalHistory', back_populates='approval_request', cascade='all, delete-orphan', lazy='dynamic')
    comments = db.relationship('ApprovalComment', back_populates='approval_request', cascade='all, delete-orphan', lazy='dynamic')

    def is_sla_breached(self):
        """Check if SLA is breached"""
        if not self.sla_due_at:
            return False
        if self.approval_status in ['Approved', 'Rejected']:
            return False
        sla_due = self.sla_due_at
        if sla_due.tzinfo is not None:
            now = datetime.now(timezone.utc)
        else:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
        return now > sla_due

    def sla_remaining_seconds(self):
        """Get remaining seconds until SLA due"""
        if not self.sla_due_at:
            return None
        if self.approval_status in ['Approved', 'Rejected']:
            return 0
        sla_due = self.sla_due_at
        if sla_due.tzinfo is not None:
            now = datetime.now(timezone.utc)
        else:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
        remaining = sla_due - now
        return max(0, int(remaining.total_seconds()))

    def to_dict(self):
        return {
            'id': self.id,
            'approval_type': self.approval_type,
            'module_name': self.module_name,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'request_title': self.request_title,
            'request_description': self.request_description,
            'requested_by': self.requested_by.username if self.requested_by else None,
            'assigned_approver': self.assigned_approver.username if self.assigned_approver else None,
            'priority': self.priority,
            'approval_status': self.approval_status,
            'sla_due_at': self.sla_due_at.isoformat() if self.sla_due_at else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejected_at': self.rejected_at.isoformat() if self.rejected_at else None,
            'escalated_at': self.escalated_at.isoformat() if self.escalated_at else None,
            'is_sla_breached': self.is_sla_breached(),
            'sla_remaining_seconds': self.sla_remaining_seconds(),
        }

    def __repr__(self):
        return f'<ApprovalRequest {self.id} {self.approval_type} {self.approval_status}>'


class ApprovalWorkflow(db.Model):
    """
    Defines approval workflow levels and escalation rules.
    Supports multi-level approval chains.
    """
    __tablename__ = 'approval_workflows'
    __table_args__ = (
        db.Index('idx_approval_workflows_approval_type', 'approval_type'),
        db.Index('idx_approval_workflows_role_id', 'role_id'),
        db.UniqueConstraint('approval_type', 'approval_level', name='uix_approval_type_level'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    
    # Workflow Configuration
    approval_type = db.Column(db.String(50), nullable=False, index=True)
    approval_level = db.Column(db.Integer, nullable=False)
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Escalation Rules
    escalation_after_minutes = db.Column(db.Integer, default=1440, nullable=False)
    auto_escalate = db.Column(db.Boolean, default=False, nullable=False)
    
    # Status
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    role = db.relationship('Role', foreign_keys=[role_id], lazy='joined')

    def __repr__(self):
        return f'<ApprovalWorkflow {self.approval_type} Level {self.approval_level}>'


class ApprovalHistory(db.Model):
    """
    Audit trail for all approval actions.
    Immutable record of every approval decision.
    """
    __tablename__ = 'approval_histories'
    __table_args__ = (
        db.Index('idx_approval_histories_approval_request_id', 'approval_request_id'),
        db.Index('idx_approval_histories_action_by', 'action_by_id'),
        db.Index('idx_approval_histories_action_time', 'action_time'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    
    # Audit Information
    approval_request_id = db.Column(db.String(36), db.ForeignKey('approval_requests.id', ondelete='CASCADE'), nullable=False, index=True)
    action_taken = db.Column(db.String(50), nullable=False)
    action_by_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Status Change
    previous_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=True)
    
    # Details
    remarks = db.Column(db.Text, nullable=True)
    action_time = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    approval_request = db.relationship('ApprovalRequest', back_populates='history', foreign_keys=[approval_request_id])
    action_by = db.relationship('User', foreign_keys=[action_by_id], lazy='joined')

    def __repr__(self):
        return f'<ApprovalHistory {self.id} {self.action_taken}>'


class ApprovalComment(db.Model):
    """
    Comments on approval requests.
    Enables collaboration during approval process.
    """
    __tablename__ = 'approval_comments'
    __table_args__ = (
        db.Index('idx_approval_comments_approval_request_id', 'approval_request_id'),
        db.Index('idx_approval_comments_user_id', 'user_id'),
        db.Index('idx_approval_comments_created_at', 'created_at'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    
    # Comment Details
    approval_request_id = db.Column(db.String(36), db.ForeignKey('approval_requests.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    comment = db.Column(db.Text, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    approval_request = db.relationship('ApprovalRequest', back_populates='comments', foreign_keys=[approval_request_id])
    user = db.relationship('User', foreign_keys=[user_id], lazy='joined')

    def __repr__(self):
        return f'<ApprovalComment {self.id}>'
