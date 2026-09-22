"""Schemas Pydantic para autenticación (RF-1, RF-4)."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Solicitud de login. Solo email y password, nunca el hash."""

    email: str
    password: str


class LoginResponse(BaseModel):
    """Respuesta de login con token Bearer."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Payload mínimo del JWT: solo sub (email) y exp."""

    sub: str
    exp: int
