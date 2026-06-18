import hashlib
from datetime import datetime

from sqlalchemy import func

from app.extensions import db
from app.modules.auth.models import (
    AuditLog,
    LoginAttempt,
    RefreshToken,
    RememberToken,
    Role,
    User,
    UserSession,
)


class AuthRepository:
    def get_user_by_id(self, user_id):
        return User.query.filter_by(id=user_id).first()

    def find_user_by_credential(self, identifier):
        normalized_identifier = (identifier or '').strip().lower()
        return (
            User.query.filter(func.lower(User.email) == normalized_identifier).first()
            or User.query.filter(func.lower(User.username) == normalized_identifier).first()
            or User.query.filter_by(phone=identifier).first()
        )

    def get_role_by_name(self, name):
        return Role.query.filter_by(name=name).first()

    def fetch_permissions(self, user):
        return user.permissions if user else []

    def save_login_attempt(self, user, identifier, ip_address, user_agent, success, reason=None):
        attempt = LoginAttempt(
            user_id=user.id if user else None,
            identifier=identifier,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            reason=reason,
        )
        db.session.add(attempt)
        db.session.commit()
        return attempt

    def save_audit_log(self, user, action, ip_address, user_agent, device_info=None, metadata=None):
        log = AuditLog(
            user_id=user.id if user else None,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            details=metadata,
        )
        db.session.add(log)
        db.session.commit()
        return log

    def create_session(self, user, session_key, ip_address, user_agent, device_info, remember_me, expires_at):
        session = UserSession(
            user_id=user.id,
            session_key=session_key,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            remember_me=remember_me,
            expires_at=expires_at,
            active=True,
            revoked=False,
        )
        db.session.add(session)
        db.session.commit()
        return session

    def revoke_session(self, session_key):
        session = UserSession.query.filter_by(session_key=session_key).first()
        if session:
            session.revoked = True
            session.active = False
            db.session.commit()
        return session

    def get_active_session(self, session_key):
        return UserSession.query.filter_by(session_key=session_key, active=True, revoked=False).first()

    def save_refresh_token(self, jti, user, token_hash, expires_at, ip_address, user_agent):
        refresh_token = RefreshToken(
            jti=jti,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            revoked=False,
        )
        db.session.add(refresh_token)
        db.session.commit()
        return refresh_token

    def get_refresh_token(self, jti):
        return RefreshToken.query.filter_by(jti=jti).first()

    def revoke_refresh_token(self, jti):
        token = self.get_refresh_token(jti)
        if token:
            token.revoked = True
            db.session.commit()
        return token

    def revoke_all_refresh_tokens(self, user):
        RefreshToken.query.filter_by(user_id=user.id, revoked=False).update({'revoked': True})
        db.session.commit()

    def save_remember_token(self, user, token_hash, expires_at, ip_address, user_agent, device_info=None):
        remember_token = RememberToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            revoked=False,
        )
        db.session.add(remember_token)
        db.session.commit()
        return remember_token

    def get_remember_token(self, token_hash):
        return RememberToken.query.filter_by(token_hash=token_hash).first()

    def revoke_remember_tokens(self, user):
        RememberToken.query.filter_by(user_id=user.id, revoked=False).update({'revoked': True})
        db.session.commit()

    def update_user(self, user):
        db.session.add(user)
        db.session.commit()
        return user

    def get_user_sessions(self, user):
        return UserSession.query.filter_by(user_id=user.id).all()

    def get_user_by_email(self, email):
        return User.query.filter(func.lower(User.email) == email.lower()).first()

    def get_user_by_username(self, username):
        return User.query.filter(func.lower(User.username) == username.lower()).first()

