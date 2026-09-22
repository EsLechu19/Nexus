"""Dependency de autenticación — valida JWT antes de cualquier acceso a BD (RF-2)."""

from fastapi import Header, HTTPException

from app.services.auth_service import validar_token


def get_current_user(
    authorization: str | None = Header(default=None),  # type: ignore[assignment]
) -> str:
    """Valida `Authorization: Bearer <token>` y retorna email (sub).

    Exige prefijo `Bearer ` case-sensitive. Si falta, vacío, `Basic`,
    `Bearer` sin token, firma alterada o `exp` expirado → 401.
    No abre conexión a base de datos ni hace consulta SQL (orden antes de lock, spec corregida).
    """
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization[len("Bearer ") :]
    if not token or not token.strip():
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = validar_token(token.strip())
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Not authenticated") from exc

    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return sub
