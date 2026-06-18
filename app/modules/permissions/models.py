"""
Permission Management Models

Extends the base Permission model with enterprise features:
- Module-level access control
- Scope-based permissions
- Workflow permissions
- Permission audit trails
"""

import uuid
from datetime import datetime, timezone

from app.extensions import db


def make_uuid():
    return str(uuid.uuid4())


class PermissionDetail(db.Model):
    """
    Extended Permission Details
    Adds module, action, scope, and security level information
    """
    __tablename__ = 'permission_details'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    permission_id = db.Column(db.String(36), db.ForeignKey('permissions.id'), unique=True, nullable=False, index=True)
    module = db.Column(db.String(120), nullable=False)  # users, vehicles, deployments, etc.
    action = db.Column(db.String(80), nullable=False)  # view, create, edit, delete, approve, export, assign, block, override
    scope_type = db.Column(db.String(50), default='global', nullable=False)  # global, company, circle, client, project, subzone
    security_level = db.Column(db.String(20), default='medium', nullable=False)  # low, medium, critical
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    can_delegate = db.Column(db.Boolean, default=False)
    requires_mfa = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.String(36), nullable=True)  # User ID who created this permission
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    permission = db.relationship('Permission', backref=db.backref('detail', uselist=False), uselist=False)

    def __repr__(self):
        return f'<PermissionDetail {self.module}.{self.action}>'


class PermissionWorkflowAccess(db.Model):
    """
    Workflow-specific permission attributes
    Links permissions to workflow actions (approve, reject, escalate, override)
    """
    __tablename__ = 'permission_workflow_access'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    permission_id = db.Column(db.String(36), db.ForeignKey('permissions.id'), unique=True, nullable=False, index=True)
    workflow_type = db.Column(db.String(120), nullable=False)  # deployment, attendance, approval_chain, etc.
    can_approve = db.Column(db.Boolean, default=False)
    can_reject = db.Column(db.Boolean, default=False)
    can_escalate = db.Column(db.Boolean, default=False)
    can_override = db.Column(db.Boolean, default=False)
    can_close_workflow = db.Column(db.Boolean, default=False)
    approval_level = db.Column(db.Integer, default=0)  # 0=none, 1=first, 2=second, 3=final
    auto_approve_threshold = db.Column(db.Float, nullable=True)  # for amount-based approvals
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    permission = db.relationship('Permission', backref=db.backref('workflow_access', uselist=False), uselist=False)

    def __repr__(self):
        return f'<PermissionWorkflowAccess {self.permission_id}:{self.workflow_type}>'


class PermissionCategory(db.Model):
    """
    Logical grouping of permissions by category
    Replaces the older PermissionGroup for better organization
    """
    __tablename__ = 'permission_category'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    name = db.Column(db.String(120), unique=True, nullable=False)
    code = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    icon = db.Column(db.String(50), nullable=True)  # Bootstrap icon class
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    permissions = db.relationship('Permission', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<PermissionCategory {self.name}>'


class PermissionAuditLog(db.Model):
    """
    Audit trail for permission changes, assignments, and access violations
    """
    __tablename__ = 'permission_audit_log'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    permission_id = db.Column(db.String(36), db.ForeignKey('permissions.id'), nullable=True, index=True)
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=True, index=True)
    user_id = db.Column(db.String(36), nullable=True)  # User who triggered the action
    action = db.Column(db.String(120), nullable=False)  # created, updated, deleted, assigned, revoked, accessed, denied, etc.
    entity_type = db.Column(db.String(80), nullable=False)  # 'permission', 'role', 'user', 'access_violation', etc.
    entity_id = db.Column(db.String(36), nullable=True)
    action_type = db.Column(db.String(50), nullable=False)  # 'permission_change', 'role_assignment', 'access_attempt', 'security_event'
    status = db.Column(db.String(20), default='success', nullable=False)  # success, failure, unauthorized, blocked
    old_value = db.Column(db.JSON, nullable=True)
    new_value = db.Column(db.JSON, nullable=True)
    reason = db.Column(db.String(255), nullable=True)  # Reason for deny/revoke
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    severity = db.Column(db.String(20), default='info', nullable=False)  # info, warning, critical
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    permission = db.relationship('Permission', backref='audit_logs')
    role = db.relationship('Role', backref='permission_audit_logs')

    def __repr__(self):
        return f'<PermissionAuditLog {self.action}:{self.entity_type}>'


class PermissionScope(db.Model):
    """
    Scope restrictions for permissions
    Maps permissions to specific organizational scopes
    """
    __tablename__ = 'permission_scope'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    permission_id = db.Column(db.String(36), db.ForeignKey('permissions.id'), nullable=False, index=True)
    scope_code = db.Column(db.String(50), nullable=False)  # global, company_id, circle_id, client_id, project_id, subzone_id
    scope_value = db.Column(db.String(36), nullable=True)  # The actual ID if scoped to specific entity
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    permission = db.relationship('Permission', backref='scopes')

    def __repr__(self):
        return f'<PermissionScope {self.permission_id}:{self.scope_code}>'


class RolePermissionMatrix(db.Model):
    """
    Role-Permission mapping matrix for quick access and analytics
    Denormalized table for performance
    """
    __tablename__ = 'role_permission_matrix'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=False, index=True)
    permission_id = db.Column(db.String(36), db.ForeignKey('permissions.id'), nullable=False, index=True)
    inherited_from = db.Column(db.String(36), nullable=True)  # Parent role ID if inherited
    is_inherited = db.Column(db.Boolean, default=False)
    can_delegate = db.Column(db.Boolean, default=False)
    assigned_by = db.Column(db.String(36), nullable=True)  # User ID who assigned this
    assigned_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)  # For temporary assignments
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    role = db.relationship('Role', backref='permission_matrix')
    permission = db.relationship('Permission', backref='role_matrix')

    __table_args__ = (db.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'), )

    def __repr__(self):
        return f'<RolePermissionMatrix {self.role_id}:{self.permission_id}>'
