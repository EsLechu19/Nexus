"""Fixtures compartidos para autenticación (T10, Impacto 001-004, RNF-6)."""

import os
import uuid

import pytest

# Importar todos los modelos para que Base.metadata conozca todas las tablas
# antes de cualquier Base.metadata.create_all en tests aislados
from app.models import (
    movimiento_inventario,  # noqa: F401
    producto,  # noqa: F401
    proveedor,  # noqa: F401
    usuario,  # noqa: F401
)
from app.services.auth_service import crear_token


@pytest.fixture(scope="function")
def auth_headers(monkeypatch):
    """Fixture que retorna header Authorization Bearer válido para tests 001-004.

    Crea un email único test_011_{uuid}@tienda.com y genera un JWT válido
    vía auth_service.crear_token, sin necesidad de INSERT en DB (JWT stateless,
    RNF-8). Establece JWT_SECRET_KEY de test si no existe.
    """
    # Asegurar secreto de test (32+ chars para evitar InsecureKeyLengthWarning)
    if not os.getenv("JWT_SECRET_KEY"):
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T10-32chars-minimo!!")
    # También soportar monkeypatch ya seteado
    email = f"test_011_{uuid.uuid4().hex[:8]}@tienda.com"
    token = crear_token(email)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def auth_headers_admin(monkeypatch):
    """Variante con email fijo admin para tests que necesitan admin@tienda.com."""
    if not os.getenv("JWT_SECRET_KEY"):
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T10-32chars-minimo!!")
    token = crear_token("admin@tienda.com")
    return {"Authorization": f"Bearer {token}"}
