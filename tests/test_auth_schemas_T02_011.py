"""Tests de T02 — Schemas Pydantic de auth (RF-1, RF-4, RNF-4) — TDD."""

import pytest
from pydantic import ValidationError


def test_schemas_existen():
    """T02: app/schemas/auth.py define LoginRequest, LoginResponse, TokenPayload."""
    from app.schemas.auth import LoginRequest, LoginResponse, TokenPayload

    assert LoginRequest is not None
    assert LoginResponse is not None
    assert TokenPayload is not None


def test_login_request_requiere_email_y_password():
    """T02: LoginRequest exige email y password requeridos."""
    from app.schemas.auth import LoginRequest

    # válido
    req = LoginRequest(email="admin@tienda.com", password="secreto123")
    assert req.email == "admin@tienda.com"
    assert req.password == "secreto123"

    # falta email -> 422
    with pytest.raises(ValidationError) as exc:
        LoginRequest(password="secreto123")  # type: ignore[call-arg]
    assert "email" in str(exc.value).lower()

    # falta password -> 422
    with pytest.raises(ValidationError) as exc2:
        LoginRequest(email="admin@tienda.com")  # type: ignore[call-arg]
    assert "password" in str(exc2.value).lower()


def test_login_request_no_expone_password_hash():
    """T02: LoginRequest no debe tener campo password_hash."""
    from app.schemas.auth import LoginRequest

    assert "password_hash" not in LoginRequest.model_fields
    # tampoco expone modelo
    fields = set(LoginRequest.model_fields.keys())
    assert fields == {"email", "password"}


def test_login_response_campos():
    """T02: LoginResponse con access_token y token_type bearer."""
    from app.schemas.auth import LoginResponse

    resp = LoginResponse(access_token="abc123", token_type="bearer")
    assert resp.access_token == "abc123"
    assert resp.token_type == "bearer"
    assert "password" not in LoginResponse.model_fields
    assert "password_hash" not in LoginResponse.model_fields


def test_token_payload_campos():
    """T02: TokenPayload con sub y exp."""
    from app.schemas.auth import TokenPayload

    payload = TokenPayload(sub="admin@tienda.com", exp=1234567890)
    assert payload.sub == "admin@tienda.com"
    assert payload.exp == 1234567890
    assert set(TokenPayload.model_fields.keys()) == {"sub", "exp"}
