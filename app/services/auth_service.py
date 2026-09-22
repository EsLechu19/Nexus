"""Service de autenticación — hasheo, validación de email y JWT (RF-1, RF-4, RF-5, RNF-1, RNF-2, RNF-3)."""

import os
import re
from datetime import datetime, timedelta, timezone

import hashlib

import bcrypt  # type: ignore[import-untyped]
import jwt  # type: ignore[import-untyped]

# Regex sintáctico de email como en 002-proveedores (sin verificar dominio).
_EMAIL_REGEX = re.compile(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$")


def normalizar_email(email: str) -> str:
    """Normaliza email con trim y minúsculas.

    Respeta validación de 002 (trim en extremos + lower).
    """
    return email.strip().lower()


def validar_email_formato(email: str) -> bool:
    """Valida formato sintáctico de email (sin verificar dominio).

    Tras trim+lower: local 1-64, dominio con al menos un punto, TLD >=2,
    longitud total <=254, un solo @, sin espacios.
    """
    if not isinstance(email, str):
        return False
    normalizado = email.strip().lower()
    if not normalizado or len(normalizado) > 254:
        return False
    if normalizado.count("@") != 1:
        return False
    local, dominio = normalizado.split("@", 1)
    if not local or len(local) > 64:
        return False
    if "." not in dominio:
        return False
    if " " in normalizado:
        return False
    return bool(_EMAIL_REGEX.fullmatch(normalizado))


def _prehash_bcrypt(password: str) -> bytes:
    """Pre-hash a SHA256 hexdigest si >72 bytes para bcrypt.

    bcrypt solo procesa 72 bytes; bcrypt 4.x levanta ValueError si >72.
    Se usa sha256 hexdigest (64 chars ASCII, siempre <72) para long passwords.
    Compatible entre hash y verify. Retorna bytes listos para bcrypt.
    """
    b = password.encode("utf-8")
    if len(b) > 72:
        # hexdigest es 64 chars ASCII, siempre <72 bytes
        return hashlib.sha256(b).hexdigest().encode("utf-8")
    return b


def hash_password(password: str) -> str:
    """Hashea contraseña en claro con bcrypt (cost 12, salt automático).

    Nunca loguea el claro ni el hash.
    Usa bcrypt directo (sin passlib) para evitar incompatibilidad
    passlib 1.7.4 + bcrypt 4.x (__about__ y límite 72 bytes).
    """
    pre = _prehash_bcrypt(password)
    hashed: bytes = bcrypt.hashpw(pre, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    """Verifica contraseña en claro contra hash bcrypt.

    Retorna True si coincide, False si no.
    Soporta hashes previos generados con passlib+bcrypt (mismo formato $2b$).
    """
    try:
        pre = _prehash_bcrypt(password)
        return bcrypt.checkpw(pre, password_hash.encode("utf-8"))
    except Exception:
        return False


# Alias compatibilidad con versión previa (pre-hash con passlib)
def _truncar_bcrypt(password: str) -> str:
    """Compat: retorna str pre-hasheado (hexdigest si >72) para tests legacy."""
    b = _prehash_bcrypt(password)
    # _prehash retorna bytes; si fue sha256 hexdigest, decodifica a str
    return b.decode("utf-8")


def _obtener_secret() -> str:
    """Obtiene JWT_SECRET_KEY de variable de entorno, nunca hardcodeado."""
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        # Fallback a SECRET_KEY por compatibilidad, pero nunca valor por defecto hardcodeado en código
        secret = os.getenv("SECRET_KEY", "")
    if not secret:
        raise ValueError("JWT_SECRET_KEY no configurado")
    return secret


def crear_token(email: str) -> str:
    """Crea JWT HS256 con sub=email normalizado y exp en 8 horas (UTC).

    Lee JWT_SECRET_KEY de env var, nunca hardcodeado (RNF-2, AGENTS.md:30).
    """
    email_norm = normalizar_email(email)
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=8)
    payload = {
        "sub": email_norm,
        "exp": int(exp.timestamp()),
    }
    secret = _obtener_secret()
    token: str = jwt.encode(payload, secret, algorithm="HS256")
    return token


def validar_token(token: str) -> dict:
    """Valida JWT HS256 con firma y exp, retorna payload.

    Verifica con PyJWT algorithms=["HS256"] y exp. Si inválido/expirado, lanza excepción.
    """
    secret = _obtener_secret()
    # jwt.decode verifica exp automáticamente y levanta ExpiredSignatureError / InvalidSignatureError
    payload: dict = jwt.decode(token, secret, algorithms=["HS256"])
    return payload
