"""Router de autenticación — solo HTTP y validación Pydantic (RF-1, RF-3)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import (
    crear_token,
    normalizar_email,
    validar_email_formato,
    verificar_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(datos: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """Inicio de sesión con regla de dos niveles (RF-1).

    - email/password ausentes → 422 vía Pydantic (LoginRequest requerido).
    - Cualquier otro caso (formato inválido, no existe, incorrecta) → 401 genérico.
    - Éxito → 200 con JWT Bearer 8h.
    """
    # Regla de dos niveles: formato inválido debe ser 401, no 422
    if not validar_email_formato(datos.email):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas"
        )

    email_norm = normalizar_email(datos.email)

    usuario = db.query(Usuario).filter(Usuario.email == email_norm).first()
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas"
        )

    if not verificar_password(datos.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas"
        )

    token = crear_token(email_norm)
    return LoginResponse(access_token=token, token_type="bearer")
