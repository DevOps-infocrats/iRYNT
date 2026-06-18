from dataclasses import dataclass
from typing import Optional, Dict, List


@dataclass
class LoginRequestDTO:
    identifier: str
    password: str
    remember_me: bool = False


@dataclass
class ForgotPasswordDTO:
    email: str


@dataclass
class ResetPasswordDTO:
    token: str
    new_password: str


@dataclass
class RefreshTokenDTO:
    refresh_token: str


@dataclass
class AuthResponseDTO:
    success: bool
    message: str
    data: Optional[Dict] = None

