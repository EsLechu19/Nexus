"""Tests de T05 — dependency get_current_user (RF-2) — TDD."""

import time

import jwt
import pytest
from fastapi import HTTPException


def test_get_current_user_valido(monkeypatch):
    """T05: get_current_user con Bearer válido retorna sub."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-deps-T05-32chars!!")
    from app.services.auth_service import crear_token
    from app.services.deps import get_current_user

    token = crear_token("admin@tienda.com")
    email = get_current_user(authorization=f"Bearer {token}")
    assert email == "admin@tienda.com"


def test_get_current_user_falta_header(monkeypatch):
    """T05: sin header, vacío, sin Bearer, Basic, Bearer sin token → 401."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-deps-T05-32chars!!")
    from app.services.deps import get_current_user

    for header in [None, "", "Basic abc", "Bearer", "Bearer ", "Bearer    "]:
        with pytest.raises(HTTPException) as exc:
            get_current_user(authorization=header)  # type: ignore[arg-type]
        assert exc.value.status_code == 401


def test_get_current_user_case_sensitive(monkeypatch):
    """T05: prefijo Bearer es case-sensitive — 'bearer' minúsculas debe ser 401."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-deps-T05-32chars!!")
    from app.services.auth_service import crear_token
    from app.services.deps import get_current_user

    token = crear_token("admin@tienda.com")
    with pytest.raises(HTTPException) as exc:
        get_current_user(authorization=f"bearer {token}")
    assert exc.value.status_code == 401


def test_get_current_user_firma_invalida_y_expirado(monkeypatch):
    """T05: firma alterada y exp expirado → 401."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-deps-T05-32chars!!")
    from app.services.auth_service import crear_token
    from app.services.deps import get_current_user

    token = crear_token("admin@tienda.com")
    alterado = token[:-1] + ("a" if token[-1] != "a" else "b")
    with pytest.raises(HTTPException) as exc:
        get_current_user(authorization=f"Bearer {alterado}")
    assert exc.value.status_code == 401

    # expirado
    payload = {"sub": "admin@tienda.com", "exp": int(time.time()) - 10}
    expirado = jwt.encode(payload, "test-secret-deps-T05-32chars!!", algorithm="HS256")
    with pytest.raises(HTTPException) as exc2:
        get_current_user(authorization=f"Bearer {expirado}")
    assert exc2.value.status_code == 401


def test_get_current_user_no_abre_session():
    """T05: get_current_user no debe abrir Session ni hacer SELECT."""
    from pathlib import Path

    content = Path("app/services/deps.py").read_text(encoding="utf-8")
    assert "Session" not in content
    assert "SELECT" not in content
    assert "get_db" not in content
    # debe importar validar_token y usarlo
    assert "validar_token" in content
