import uuid
from datetime import datetime, timedelta, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.domain.auth.access import AccessManager
from app.extensions import db


def make_uuid():
    return str(uuid.uuid4())


role_permissions = db.Table(
    'role_permissions',
    db.Column('role_id', db.String(36), db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.String(36), db.ForeignKey('permissions.id'), primary_key=True),
)


user_roles = db.Table(
    'user_roles',
    db.Column('user_id', db.String(36), db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.String(36), db.ForeignKey('roles.id'), primary_key=True),
)


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    is_system = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    permissions = db.relationship(
        'Permission', secondary=role_permissions, back_populates='roles'
    )
    users = db.relationship('User', secondary=user_roles, back_populates='roles')

    def __repr__(self):
        return f'<Role {self.name}>'


class Permission(db.Model):
    __tablename__ = 'permissions'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    category_id = db.Column(db.String(36), db.ForeignKey('permission_category.id'), nullable=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    roles = db.relationship('Role', secondary=role_permissions, back_populates='permissions')

    def __repr__(self):
        return f'<Permission {self.name}>'


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(24), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=True, index=True)
    primary_role = db.relationship('Role', foreign_keys=[role_id])
    company_id = db.Column(db.String(36), nullable=True, index=True)
    circle_id = db.Column(db.String(36), nullable=True, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime(timezone=True), nullable=True)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)
    password_changed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    roles = db.relationship('Role', secondary=user_roles, back_populates='users')
    sessions = db.relationship('UserSession', back_populates='user', lazy='dynamic')
    refresh_tokens = db.relationship('RefreshToken', back_populates='user', lazy='dynamic')
    login_attempts = db.relationship('LoginAttempt', back_populates='user', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', back_populates='user', lazy='dynamic')
    remember_tokens = db.relationship('RememberToken', back_populates='user', lazy='dynamic')
    driver_profile = db.relationship('DriverProfile', back_populates='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
        self.password_changed_at = datetime.now(timezone.utc)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_locked(self):
        if self.locked_until is None:
            return False
        now = datetime.now(timezone.utc)
        locked_until = self.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        return locked_until > now

    @property
    def is_superadmin(self):
        if self.primary_role and self.primary_role.name.lower() == 'super admin':
            return True
        return any(role.name.lower() == 'super admin' for role in self.roles)

    @property
    def role_names(self):
        names = []
        if self.primary_role and self.primary_role.name:
            names.append(self.primary_role.name.lower())
        names.extend([role.name.lower() for role in self.roles if role.name])
        return names

    @property
    def role_level(self):
        from app.domain.auth.access import ROLE_HIERARCHY

        levels = [ROLE_HIERARCHY.get(name, 0) for name in self.role_names]
        return max(levels, default=0)

    def has_role(self, roles):
        return AccessManager(self).has_role(roles)

    def has_permission(self, permission_name):
        return AccessManager(self).has_permission(permission_name)

    def has_scope(
        self,
        company_id=None,
        circle_id=None,
        client_id=None,
        project_id=None,
        subzone_id=None,
    ):
        return AccessManager(self).has_scope(
            company_id=company_id,
            circle_id=circle_id,
            client_id=client_id,
            project_id=project_id,
            subzone_id=subzone_id,
        )

    @property
    def permissions(self):
        if self.is_superadmin:
            return ['*']
        return AccessManager(self).get_permissions()

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'company_id': self.company_id,
            'circle_id': self.circle_id,
            'role': self.primary_role.name if self.primary_role else None,
            'permissions': self.permissions,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'last_login_ip': self.last_login_ip,
            'driver_profile_id': self.driver_profile.id if self.driver_profile else None,
        }

    def __repr__(self):
        return f'<User {self.email}>'


class UserSession(db.Model):
    __tablename__ = 'user_sessions'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    session_key = db.Column(db.String(128), nullable=False, unique=True, index=True)
    user_agent = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    device_info = db.Column(db.String(255), nullable=True)
    remember_me = db.Column(db.Boolean, default=False, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    revoked = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship('User', back_populates='sessions')

    def is_active_session(self):
        now = datetime.now(timezone.utc)
        expires_at = self.expires_at
        if expires_at is None:
            return self.active and not self.revoked
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return self.active and not self.revoked and expires_at > now


class LoginAttempt(db.Model):
    __tablename__ = 'login_attempts'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True, index=True)
    identifier = db.Column(db.String(120), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    success = db.Column(db.Boolean, default=False, nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', back_populates='login_attempts')


class RefreshToken(db.Model):
    __tablename__ = 'refresh_tokens'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    jti = db.Column(db.String(120), unique=True, nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    token_hash = db.Column(db.String(128), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    revoked = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)

    user = db.relationship('User', back_populates='refresh_tokens')

    def is_active_token(self):
        now = datetime.now(timezone.utc)
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return not self.revoked and expires_at > now


class RememberToken(db.Model):
    __tablename__ = 'remember_tokens'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    token_hash = db.Column(db.String(128), nullable=False, unique=True, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    device_info = db.Column(db.String(255), nullable=True)
    revoked = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)

    user = db.relationship('User', back_populates='remember_tokens')

    def is_valid(self):
        now = datetime.now(timezone.utc)
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return not self.revoked and expires_at > now


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True, index=True)
    action = db.Column(db.String(120), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    device_info = db.Column(db.String(255), nullable=True)
    details = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', back_populates='audit_logs')

