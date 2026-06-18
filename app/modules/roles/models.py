import uuid
from datetime import datetime, timezone

from app.extensions import db


def make_uuid():
    return str(uuid.uuid4())


# Extended Role model fields (extending app.modules.auth.models.Role)
# This is for roles module-specific enhancements

permission_groups = db.Table(
    'permission_groups',
    db.Column('role_id', db.String(36), db.ForeignKey('roles.id'), primary_key=True),
    db.Column('group_id', db.String(36), db.ForeignKey('permission_group.id'), primary_key=True),
)

permission_group_permissions = db.Table(
    'permission_group_permissions',
    db.Column('group_id', db.String(36), db.ForeignKey('permission_group.id'), primary_key=True),
    db.Column('permission_id', db.String(36), db.ForeignKey('permissions.id'), primary_key=True),
)


class PermissionGroup(db.Model):
    """Logical grouping of related permissions for cleaner UI"""
    __tablename__ = 'permission_group'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    name = db.Column(db.String(120), unique=True, nullable=False)
    code = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(80), nullable=False)  # operational, reporting, deployment, attendance, workflow, etc.
    permissions_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    permissions = db.relationship(
        'Permission',
        secondary=permission_group_permissions,
        backref='permission_groups',
        lazy='dynamic',
    )

    def __repr__(self):
        return f'<PermissionGroup {self.name}>'


class WorkflowPermission(db.Model):
    """Workflow authority for roles (approvals, rejections, escalations)"""
    __tablename__ = 'workflow_permissions'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=False, index=True)
    workflow_type = db.Column(db.String(120), nullable=False)  # deployment, attendance, compliance, etc.
    can_approve = db.Column(db.Boolean, default=False)
    can_reject = db.Column(db.Boolean, default=False)
    can_escalate = db.Column(db.Boolean, default=False)
    can_override = db.Column(db.Boolean, default=False)
    can_close_workflow = db.Column(db.Boolean, default=False)
    approval_level = db.Column(db.Integer, default=0)  # 0=none, 1=first, 2=second, 3=final
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    role = db.relationship('Role', backref='workflow_permissions')

    def __repr__(self):
        return f'<WorkflowPermission {self.role_id}:{self.workflow_type}>'


class RoleHierarchy(db.Model):
    """Role hierarchy levels (L1-L13 system)"""
    __tablename__ = 'role_hierarchy'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=False, unique=True, index=True)
    level = db.Column(db.Integer, nullable=False, unique=True)  # 1-13
    tier = db.Column(db.String(50), nullable=False)  # 'field', 'circle', 'corporate', 'system'
    parent_level = db.Column(db.Integer, nullable=True)  # for inheritance
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    role = db.relationship('Role', backref='hierarchy')

    def __repr__(self):
        return f'<RoleHierarchy L{self.level}:{self.role_id}>'


class ScopeType(db.Model):
    """Scope types for access control (Global, Company, Circle, etc.)"""
    __tablename__ = 'scope_type'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    code = db.Column(db.String(80), unique=True, nullable=False)  # 'global', 'company', 'circle', 'client', 'project', 'subzone'
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    level = db.Column(db.Integer, nullable=False)  # ordering of scope levels
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f'<ScopeType {self.code}>'


class RoleScope(db.Model):
    """Which scopes a role can access"""
    __tablename__ = 'role_scope'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=False, index=True)
    scope_type_id = db.Column(db.String(36), db.ForeignKey('scope_type.id'), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    role = db.relationship('Role', backref='scopes')
    scope_type = db.relationship('ScopeType')

    def __repr__(self):
        return f'<RoleScope {self.role_id}:{self.scope_type.code}>'


class ModuleAccess(db.Model):
    """Module-level access matrix for roles"""
    __tablename__ = 'module_access'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=False, index=True)
    module_name = db.Column(db.String(120), nullable=False)  # users, deployments, vehicles, etc.
    can_view = db.Column(db.Boolean, default=False)
    can_create = db.Column(db.Boolean, default=False)
    can_edit = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)
    can_approve = db.Column(db.Boolean, default=False)
    can_export = db.Column(db.Boolean, default=False)
    can_assign = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    role = db.relationship('Role', backref='module_access')

    def __repr__(self):
        return f'<ModuleAccess {self.role_id}:{self.module_name}>'


class RoleAuditLog(db.Model):
    """Audit trail for role and permission changes"""
    __tablename__ = 'role_audit_log'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=True, index=True)
    changed_by_user_id = db.Column(db.String(36), nullable=True)  # User who made the change
    action = db.Column(db.String(120), nullable=False)  # created, updated, deleted, permission_added, etc.
    entity_type = db.Column(db.String(80), nullable=False)  # 'role', 'permission', 'workflow', etc.
    entity_id = db.Column(db.String(36), nullable=True)
    old_value = db.Column(db.JSON, nullable=True)
    new_value = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def __repr__(self):
        return f'<RoleAuditLog {self.action}:{self.entity_type}>'

