from app.application.auth.controllers.auth_controller import AuthController
from app.application.auth.dto.auth_dto import ForgotPasswordDTO


class ForgotPasswordUseCase:
    def __init__(self, controller=None):
        self.controller = controller or AuthController()

    def execute(self, email):
        payload = ForgotPasswordDTO(email=email)
        return self.controller.forgot_password(payload)
