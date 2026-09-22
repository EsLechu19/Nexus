"""Tests de T11 — Unitarios auth_service hasheo, JWT, RNF-8 (RF-1, RF-4, RNF-1, RNF-2, RNF-8) — TDD."""

import time

import jwt
import pytest


def test_email_normalizado_y_formato_002(monkeypatch):
    """T11: email normalizado trim+lower, formato 002 y ≤254."""
    from app.services.auth_service import normalizar_email, validar_email_formato

    assert normalizar_email("  ADMIN@Tienda.COM ") == "admin@tienda.com"
    assert normalizar_email("  test@tienda.com  ") == "test@tienda.com"
    # formato válido
    assert validar_email_formato("admin@tienda.com") is True
    assert validar_email_formato("user.name+tag@sub.dominio.com") is True
    # inválidos
    assert validar_email_formato("sinarroba") is False
    assert validar_email_formato("sin@punto") is False
    assert validar_email_formato("a@b.c") is False  # TLD <2
    assert validar_email_formato("") is False
    # longitud >254
    largo = "a" * 250 + "@b.com"
    assert validar_email_formato(largo) is False
    # con espacios
    assert validar_email_formato("con espacios@tienda.com") is False


def test_hash_distinto_al_claro_y_salts_distintos():
    """T11: hash distinto al claro y salts distintos, nunca expone claro."""
    from app.services.auth_service import hash_password

    claro = "secreto123"
    h1 = hash_password(claro)
    h2 = hash_password(claro)
    assert h1 != claro
    assert h2 != claro
    assert h1 != h2
    assert h1.startswith("$2b$") or h1.startswith("$2a$")
    # no expone hash en asserts (solo verifica que no es igual al claro)


def test_verificar_password():
    """T11: verificar_password correcto True, incorrecto False."""
    from app.services.auth_service import hash_password, verificar_password

    claro = "secreto123"
    h = hash_password(claro)
    assert verificar_password(claro, h) is True
    assert verificar_password("erronea", h) is False
    assert verificar_password("", h) is False


def test_crear_token_sub_y_exp_aprox_8h(monkeypatch):
    """T11: crear_token con sub y exp≈now+8h."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T11-32chars-minimo!!")
    from app.services.auth_service import crear_token

    email = "Admin@Tienda.COM"
    token = crear_token(email)
    assert token.count(".") == 2
    payload = jwt.decode(
        token,
        "test-secret-T11-32chars-minimo!!",
        algorithms=["HS256"],
        options={"verify_exp": False},
    )
    assert payload["sub"] == "admin@tienda.com"
    assert "exp" in payload
    now = int(time.time())
    assert abs(payload["exp"] - (now + 28800)) < 60


def test_validar_token_firma_alterada_y_exp_pasado_falla(monkeypatch):
    """T11: validar_token con firma alterada o exp pasado → excepción (401)."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T11-32chars-minimo!!")
    from app.services.auth_service import crear_token, validar_token

    token = crear_token("admin@tienda.com")
    alterado = token[:-1] + ("a" if token[-1] != "a" else "b")
    with pytest.raises(Exception):
        validar_token(alterado)

    # exp pasado
    payload_pasado = {"sub": "admin@tienda.com", "exp": int(time.time()) - 10}
    expirado = jwt.encode(
        payload_pasado, "test-secret-T11-32chars-minimo!!", algorithm="HS256"
    )
    with pytest.raises(Exception):
        validar_token(expirado)


def test_rnf8_token_valido_tras_borrado_usuario(monkeypatch):
    """T11 RNF-8: token emitido sigue válido hasta exp aunque usuario sea borrado (stateless)."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T11-32chars-minimo!!")
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.database import Base
    from app.models.usuario import Usuario
    from app.services.auth_service import (
        crear_token,
        hash_password,
        normalizar_email,
        validar_token,
    )

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    email = "borrar@tienda.com"
    email_norm = normalizar_email(email)
    h = hash_password("secreto123")
    db = SessionLocal()
    u = Usuario(email=email_norm, password_hash=h)
    db.add(u)
    db.commit()
    db.close()

    token = crear_token(email_norm)
    # validar antes de borrar → ok
    payload = validar_token(token)
    assert payload["sub"] == email_norm

    # borrar usuario fuera de API
    db = SessionLocal()
    db.query(Usuario).filter(Usuario.email == email_norm).delete()
    db.commit()
    # usuario ya no existe
    assert db.query(Usuario).filter(Usuario.email == email_norm).first() is None
    db.close()

    # token sigue válido hasta exp (no consulta BD)
    payload2 = validar_token(token)
    assert payload2["sub"] == email_norm

    # Simular uso posterior hasta exp sigue 200 (validación sin DB)
    # No hay exponer hash
    assert "$2b$" not in token
