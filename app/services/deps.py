"""Dependency de autenticación — valida JWT antes de cualquier acceso a BD (RF-2)."""

from fastapi import Header, HTTPException

from app.services.auth_service import validar_token
from app.observability import operations_logger


def get_current_user(
    authorization: str | None = Header(default=None),  # type: ignore[assignment]
) -> str:
    """Valida `Authorization: Bearer <token>` y retorna email (sub).

    Exige prefijo `Bearer ` case-sensitive. Si falta, vacío, `Basic`,
    `Bearer` sin token, firma alterada o `exp` expirado → 401.
    No abre conexión a base de datos ni hace consulta SQL (orden antes de lock, spec corregida).
    """
    if authorization is None or not authorization.startswith("Bearer "):
        operations_logger.emit(
            "auth.failure", capability="protected-api", reason="missing-bearer"
        )
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization[len("Bearer ") :]
    if not token or not token.strip():
        operations_logger.emit(
            "auth.failure", capability="protected-api", reason="empty-bearer"
        )
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = validar_token(token.strip())
    except Exception as exc:
        operations_logger.emit(
            "auth.failure", capability="protected-api", reason="invalid-token"
        )
        raise HTTPException(status_code=401, detail="Not authenticated") from exc

    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        operations_logger.emit(
            "auth.failure", capability="protected-api", reason="invalid-subject"
        )
        raise HTTPException(status_code=401, detail="Not authenticated")
    operations_logger.emit("auth.success", capability="protected-api")
    return sub
