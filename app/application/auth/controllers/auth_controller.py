from flask import current_app
from app.application.auth.dto.auth_dto import (
    LoginRequestDTO,
    ForgotPasswordDTO,
    ResetPasswordDTO,
    RefreshTokenDTO,
)
from app.application.auth.validators.auth_validator import (
    validate_login_payload,
    validate_forgot_password_payload,
    validate_reset_password_payload,
    validate_refresh_token_payload,
)
from app.domain.auth.services.auth_service import AuthService
from app.infrastructure.repositories.auth.auth_repository import AuthRepository


class AuthController:
    def __init__(self, repository=None, service=None):
        self.repository = repository or AuthRepository()
        self.service = service or AuthService(self.repository)

    def login(self, payload: LoginRequestDTO, ip_address=None, user_agent=None):
        payload = validate_login_payload(payload)
        return self.service.authenticate(
            identifier=payload.identifier,
            password=payload.password,
            ip_address=ip_address,
            user_agent=user_agent,
            remember=payload.remember_me,
        )

    def forgot_password(self, payload: ForgotPasswordDTO):
        payload = validate_forgot_password_payload(payload)
        token = self.service.create_password_reset_token(payload.email)
        return {'success': bool(token), 'token': token}

    def reset_password(self, payload: ResetPasswordDTO):
        payload = validate_reset_password_payload(payload)
        return self.service.reset_password(payload.token, payload.new_password)

    def refresh_token(self, payload: RefreshTokenDTO):
        payload = validate_refresh_token_payload(payload)
        return self.service.refresh_access_token(payload.refresh_token)

    def revoke_tokens(self, user, refresh_token=None):
        return self.service.revoke_tokens(user, refresh_token)

