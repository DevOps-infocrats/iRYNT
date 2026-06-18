from flask import current_app, request, session
from flask_login import current_user, login_user, logout_user

from app.domain.auth.services.auth_service import AuthService
from app.infrastructure.repositories.auth.auth_repository import AuthRepository


def init_middleware(app):
    repository = AuthRepository()
    service = AuthService(repository)

    @app.before_request
    def validate_authenticated_session():
        if current_user.is_authenticated:
            session_key = session.get('auth_session_key')
            if session_key:
                active_session = repository.get_active_session(session_key)
                if not active_session:
                    logout_user()
                    session.pop('auth_session_key', None)
                    return

    @app.before_request
    def remember_me_loader():
        if current_user.is_authenticated:
            return

        remember_token = request.cookies.get('remember_me')
        if not remember_token:
            return

        user = service.validate_remember_token(remember_token)
        if not user or not user.is_active:
            return

        login_user(user, remember=True)
        session.permanent = True

    @app.after_request
    def secure_headers(response):
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault('Permissions-Policy', 'geolocation=()')
        return response
