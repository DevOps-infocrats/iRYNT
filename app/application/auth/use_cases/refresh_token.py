from app.application.auth.controllers.auth_controller import AuthController
from app.application.auth.dto.auth_dto import RefreshTokenDTO


class RefreshTokenUseCase:
    def __init__(self, controller=None):
        self.controller = controller or AuthController()

    def execute(self, refresh_token):
        payload = RefreshTokenDTO(refresh_token=refresh_token)
        return self.controller.refresh_token(payload)
