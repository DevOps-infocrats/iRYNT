from app.application.auth.controllers.auth_controller import AuthController


class LogoutUserUseCase:
    def __init__(self, controller=None):
        self.controller = controller or AuthController()

    def execute(self, user, refresh_token=None):
        return self.controller.revoke_tokens(user, refresh_token)
