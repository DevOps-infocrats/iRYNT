from app.application.auth.controllers.auth_controller import AuthController
from app.application.auth.dto.auth_dto import LoginRequestDTO


class LoginUserUseCase:
    def __init__(self, controller=None):
        self.controller = controller or AuthController()

    def execute(self, identifier, password, remember_me=False, ip_address=None, user_agent=None):
        payload = LoginRequestDTO(identifier=identifier, password=password, remember_me=remember_me)
        return self.controller.login(payload, ip_address=ip_address, user_agent=user_agent)
