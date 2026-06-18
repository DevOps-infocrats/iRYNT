from app.application.auth.use_cases.forgot_password import ForgotPasswordUseCase
from app.application.auth.use_cases.login_user import LoginUserUseCase
from app.application.auth.use_cases.logout_user import LogoutUserUseCase
from app.application.auth.use_cases.refresh_token import RefreshTokenUseCase
from app.application.auth.use_cases.reset_password import ResetPasswordUseCase


class AuthApiController:
    def __init__(self):
        self.login_use_case = LoginUserUseCase()
        self.logout_use_case = LogoutUserUseCase()
        self.refresh_use_case = RefreshTokenUseCase()
        self.forgot_use_case = ForgotPasswordUseCase()
        self.reset_use_case = ResetPasswordUseCase()

    def login(self, identifier, password, remember_me=False, ip_address=None, user_agent=None):
        return self.login_use_case.execute(
            identifier=identifier,
            password=password,
            remember_me=remember_me,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def refresh(self, refresh_token):
        return self.refresh_use_case.execute(refresh_token)

    def logout(self, refresh_token=None, user=None):
        return self.logout_use_case.execute(user=user, refresh_token=refresh_token)

    def forgot_password(self, email):
        return self.forgot_use_case.execute(email=email)

    def reset_password(self, token, new_password):
        return self.reset_use_case.execute(token=token, new_password=new_password)
