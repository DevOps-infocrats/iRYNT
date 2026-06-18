import re

from app.application.auth.dto.auth_dto import LoginRequestDTO, ForgotPasswordDTO, ResetPasswordDTO, RefreshTokenDTO


def validate_login_payload(payload: LoginRequestDTO):
    identifier = (payload.identifier or '').strip()
    password = payload.password or ''
    if not identifier or not password:
        raise ValueError('Email, username, or password cannot be empty.')
    return LoginRequestDTO(identifier=identifier, password=password, remember_me=bool(payload.remember_me))


def validate_forgot_password_payload(payload: ForgotPasswordDTO):
    email = (payload.email or '').strip().lower()
    if not email or '@' not in email:
        raise ValueError('A valid email address is required.')
    return ForgotPasswordDTO(email=email)


def validate_reset_password_payload(payload: ResetPasswordDTO):
    password = payload.new_password or ''
    if len(password) < 12:
        raise ValueError('Password must be at least 12 characters long.')
    complexity = [r'[A-Z]', r'[a-z]', r'\d', r'[^A-Za-z0-9]']
    if not all(re.search(pattern, password) for pattern in complexity):
        raise ValueError('Password must include uppercase, lowercase, numbers, and special characters.')
    return ResetPasswordDTO(token=payload.token, new_password=password)


def validate_refresh_token_payload(payload: RefreshTokenDTO):
    token = (payload.refresh_token or '').strip()
    if not token:
        raise ValueError('Refresh token is required.')
    return RefreshTokenDTO(refresh_token=token)

