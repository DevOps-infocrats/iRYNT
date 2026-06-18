from app.application.auth.controllers.auth_controller import AuthController
from app.application.auth.dto.auth_dto import ResetPasswordDTO


class ResetPasswordUseCase:
    def __init__(self, controller=None):
        self.controller = controller or AuthController()

    def execute(self, token, new_password):
        payload = ResetPasswordDTO(token=token, new_password=new_password)
        return self.controller.reset_password(payload)
