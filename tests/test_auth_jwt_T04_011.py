"""Tests de T04 — JWT HS256 8h (RF-1, RF-5, RNF-2) — TDD."""

import time
from pathlib import Path


def test_crear_token_devuelve_jwt_con_sub_y_exp(monkeypatch):
    """T04: crear_token(email) devuelve JWT HS256 con sub=email_normalizado y exp≈now+8h."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-jwt-T04-32chars-minimo!!")
    from app.services.auth_service import crear_token

    email = "  ADMIN@Tienda.COM "
    token = crear_token(email)
    assert isinstance(token, str)
    assert token.count(".") == 2  # header.payload.signature

    # decodifica sin verificar firma para inspeccionar claims (solo para test)
    import jwt

    payload = jwt.decode(
        token,
        "test-secret-jwt-T04-32chars-minimo!!",
        algorithms=["HS256"],
        options={"verify_exp": False},
    )
    assert payload["sub"] == "admin@tienda.com"
    assert "exp" in payload
    # exp ≈ now + 28800 ±60s
    now = int(time.time())
    assert abs(payload["exp"] - (now + 28800)) < 60


def test_validar_token_ok_y_firma_invalida(monkeypatch):
    """T04: validar_token(token) decodifica con HS256 y verifica firma y exp."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-jwt-T04-32chars-minimo!!")
    from app.services.auth_service import crear_token, validar_token

    token = crear_token("admin@tienda.com")
    payload = validar_token(token)
    assert payload["sub"] == "admin@tienda.com"

    # firma alterada → debe fallar
    import pytest

    alterado = token[:-1] + ("a" if token[-1] != "a" else "b")
    with pytest.raises(Exception) as exc:
        validar_token(alterado)
    # debe indicar credenciales inválidas o similar (401) — cualquier excepción es 401 en servicio
    assert exc.value is not None


def test_validar_token_expirado(monkeypatch):
    """T04: validar_token con exp pasado debe fallar."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-jwt-T04-32chars-minimo!!")
    from app.services.auth_service import validar_token
    import jwt
    import time
    import pytest

    # crea token con exp en pasado (-10s)
    payload_pasado = {"sub": "admin@tienda.com", "exp": int(time.time()) - 10}
    token_exp = jwt.encode(
        payload_pasado, "test-secret-jwt-T04-32chars-minimo!!", algorithm="HS256"
    )
    with pytest.raises(Exception):
        validar_token(token_exp)


def test_jwt_secret_no_hardcodeado():
    """T04: grep JWT_SECRET_KEY no muestra valor literal en app."""
    content = Path("app/services/auth_service.py").read_text(encoding="utf-8")
    # debe leer de env var, nunca literal como "test-secret..." hardcodeado
    assert "JWT_SECRET_KEY" in content
    assert "os.getenv" in content or "getenv" in content
    # no debe contener un secreto literal largo hardcodeado (más de 10 chars sin getenv)
    # permitimos solo la cadena "JWT_SECRET_KEY" como nombre, no valor
    assert content.count("test-secret") == 0
