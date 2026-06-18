import hashlib
import re
import uuid
from datetime import datetime, timedelta, timezone

from flask import current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jti,
)
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.infrastructure.repositories.auth.auth_repository import AuthRepository
from app.modules.auth.models import User


class AuthService:
    def __init__(self, repository=None):
        self.repository = repository or AuthRepository()

    @property
    def secret_key(self):
        return current_app.config['SECRET_KEY']

    @property
    def password_reset_expire(self):
        return current_app.config.get('PASSWORD_RESET_TOKEN_EXPIRES', 3600)

    @property
    def account_lock_threshold(self):
        return current_app.config.get('ACCOUNT_LOCK_THRESHOLD', 5)

    @property
    def account_lock_duration(self):
        return current_app.config.get('ACCOUNT_LOCK_DURATION_MINUTES', 15)

    @property
    def password_expire_days(self):
        return current_app.config.get('PASSWORD_EXPIRE_DAYS', 90)

    @property
    def remember_cookie_days(self):
        duration = current_app.config.get('REMEMBER_COOKIE_DURATION', None)
        return duration.days if duration else 30

    def _hash_token(self, raw_token):
        return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

    def _get_serializer(self):
        return URLSafeTimedSerializer(self.secret_key, salt='password-reset-salt')

    def validate_password_strength(self, password):
        if not password or len(password) < 12:
            return False
        checks = [r'[A-Z]', r'[a-z]', r'\d', r'[^A-Za-z0-9]']
        return all(re.search(pattern, password) for pattern in checks)

    def build_claims(self, user):
        return {
            'role': user.primary_role.name if user.primary_role else None,
            'permissions': user.permissions,
            'company_id': user.company_id,
            'circle_id': user.circle_id,
            'username': user.username,
        }

    def _create_tokens(self, user):
        claims = self.build_claims(user)
        access_token = create_access_token(identity=user.id, additional_claims=claims)
        refresh_token = create_refresh_token(identity=user.id, additional_claims=claims)
        return access_token, refresh_token

    def _utcnow(self):
        return datetime.now(timezone.utc)

    def _refresh_token_expiry(self):
        expires = current_app.config.get('JWT_REFRESH_TOKEN_EXPIRES')
        return self._utcnow() + expires

    def _session_expiry(self):
        return self._utcnow() + current_app.config.get('PERMANENT_SESSION_LIFETIME', timedelta(days=7))

    def _remember_token_expiry(self):
        return self._utcnow() + current_app.config.get('REMEMBER_COOKIE_DURATION', timedelta(days=30))

    def authenticate(self, identifier, password, ip_address=None, user_agent=None, remember=False):
        identifier = identifier.strip() if identifier else ''
        user = self.repository.find_user_by_credential(identifier)

        if not user:
            self.repository.save_login_attempt(
                user=None,
                identifier=identifier,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                reason='Invalid username or email',
            )
            return {'success': False, 'message': 'Invalid credentials.'}

        if not user.is_active:
            self.repository.save_login_attempt(
                user=user,
                identifier=identifier,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                reason='Inactive account',
            )
            return {'success': False, 'message': 'Account is inactive.'}

        if user.is_locked():
            return {
                'success': False,
                'message': 'Account is temporarily locked due to repeated failed attempts. Please try again later.',
            }

        if not user.check_password(password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= self.account_lock_threshold:
                user.locked_until = self._utcnow() + timedelta(minutes=self.account_lock_duration)
            self.repository.update_user(user)
            self.repository.save_login_attempt(
                user=user,
                identifier=identifier,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                reason='Invalid password',
            )
            return {'success': False, 'message': 'Invalid credentials.'}

        if not user.is_verified:
            return {'success': False, 'message': 'Email or account verification is required.'}

        if user.password_changed_at:
            password_changed_at = user.password_changed_at
            if password_changed_at.tzinfo is None:
                password_changed_at = password_changed_at.replace(tzinfo=timezone.utc)
            if self._utcnow() - password_changed_at > timedelta(days=self.password_expire_days):
                return {'success': False, 'message': 'Password has expired. Please reset your password.'}

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = self._utcnow()
        user.last_login_ip = ip_address
        self.repository.update_user(user)
        self.repository.save_login_attempt(
            user=user,
            identifier=identifier,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            reason='Login successful',
        )
        self.repository.save_audit_log(
            user=user,
            action='login.success',
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=user_agent,
            metadata={'remember_me': remember},
        )

        session_key = str(uuid.uuid4())
        self.repository.create_session(
            user=user,
            session_key=session_key,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=user_agent,
            remember_me=remember,
            expires_at=self._session_expiry(),
        )

        access_token, refresh_token = self._create_tokens(user)
        refresh_jti = get_jti(refresh_token)
        token_hash = self._hash_token(refresh_token)
        self.repository.save_refresh_token(
            jti=refresh_jti,
            user=user,
            token_hash=token_hash,
            expires_at=self._refresh_token_expiry(),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        remember_token = None
        if remember:
            raw_remember_token = str(uuid.uuid4())
            remember_token = raw_remember_token
            self.repository.save_remember_token(
                user=user,
                token_hash=self._hash_token(raw_remember_token),
                expires_at=self._remember_token_expiry(),
                ip_address=ip_address,
                user_agent=user_agent,
                device_info=user_agent,
            )

        return {
            'success': True,
            'message': 'Login successful.',
            'user': user,
            'session_key': session_key,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'remember_token': remember_token,
        }

    def create_password_reset_token(self, email):
        user = self.repository.get_user_by_email(email.lower())
        if not user:
            return None
        serializer = self._get_serializer()
        payload = {'user_id': user.id, 'email': user.email}
        return serializer.dumps(payload)

    def validate_password_reset_token(self, token):
        serializer = self._get_serializer()
        try:
            payload = serializer.loads(token, max_age=self.password_reset_expire)
            return self.repository.get_user_by_id(payload.get('user_id'))
        except SignatureExpired:
            return None
        except BadSignature:
            return None

    def reset_password(self, token, new_password):
        if not self.validate_password_strength(new_password):
            return {'success': False, 'message': 'Password does not meet complexity requirements.'}
        user = self.validate_password_reset_token(token)
        if not user:
            return {'success': False, 'message': 'Reset token is invalid or expired.'}
        user.set_password(new_password)
        user.is_verified = True
        self.repository.update_user(user)
        self.repository.save_audit_log(
            user=user,
            action='password.reset',
            ip_address=None,
            user_agent=None,
            metadata={'source': 'web'},
        )
        return {'success': True, 'message': 'Your password has been updated.'}

    def refresh_access_token(self, refresh_token):
        from flask_jwt_extended import decode_token

        try:
            decoded = decode_token(refresh_token)
        except Exception:
            return {'success': False, 'message': 'Invalid refresh token.'}

        jti = decoded.get('jti')
        stored = self.repository.get_refresh_token(jti)
        if not stored or not stored.is_active_token():
            return {'success': False, 'message': 'Refresh token is revoked or expired.'}

        user = self.repository.get_user_by_id(stored.user_id)
        access_token, new_refresh_token = self._create_tokens(user)
        self.repository.revoke_refresh_token(jti)
        refresh_jti = get_jti(new_refresh_token)
        self.repository.save_refresh_token(
            jti=refresh_jti,
            user=user,
            token_hash=self._hash_token(new_refresh_token),
            expires_at=self._refresh_token_expiry(),
            ip_address=stored.ip_address,
            user_agent=stored.user_agent,
        )

        self.repository.save_audit_log(
            user=user,
            action='token.refresh',
            ip_address=stored.ip_address,
            user_agent=stored.user_agent,
            metadata={'refresh_jti': jti},
        )

        return {
            'success': True,
            'message': 'Token refreshed successfully.',
            'access_token': access_token,
            'refresh_token': new_refresh_token,
        }

    def revoke_tokens(self, user=None, refresh_token=None):
        if refresh_token:
            from flask_jwt_extended import decode_token

            try:
                decoded = decode_token(refresh_token)
                self.repository.revoke_refresh_token(decoded.get('jti'))
                if not user:
                    user = self.repository.get_user_by_id(decoded.get('sub'))
            except Exception:
                pass

        if user:
            self.repository.revoke_all_refresh_tokens(user)
            self.repository.revoke_remember_tokens(user)
            self.repository.save_audit_log(
                user=user,
                action='logout',
                ip_address=None,
                user_agent=None,
            )

        return {'success': True, 'message': 'Session and refresh tokens revoked.'}

    def validate_remember_token(self, raw_token):
        token_hash = self._hash_token(raw_token)
        remember_token = self.repository.get_remember_token(token_hash)
        if remember_token and remember_token.is_valid():
            return self.repository.get_user_by_id(remember_token.user_id)
        return None

    def blocklisted_token(self, jwt_header, jwt_payload):
        token_type = jwt_payload.get('type')
        if token_type == 'refresh':
            jti = jwt_payload.get('jti')
            token = self.repository.get_refresh_token(jti)
            return token is not None and token.revoked
        return False

