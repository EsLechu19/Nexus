"""Tests de T07 — Router POST /api/v1/proveedores (RF-1)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models.proveedor import Proveedor  # noqa: F401


def _make_app_and_client():
    from app.routers.proveedores import router

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client


def test_post_crea_proveedor_201_normalizado(auth_headers):
    """RF-1: POST válido retorna 201 con codigo normalizado y email en minúsculas."""
    client = _make_app_and_client()
    resp = client.post(
        "/api/v1/proveedores",
        json={
            "codigo": "  prov-001 ",
            "nombre": "Distribuidora Central",
            "email": "  CONTACTO@Central.COM ",
            "telefono": "+34 912 345 678",
            "direccion": "Calle Mayor 10",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["codigo"] == "PROV-001"
    assert data["email"] == "contacto@central.com"
    assert data["nombre"] == "Distribuidora Central"
    assert data["estado"] == "activo"


def test_post_sin_contacto_201_con_nulls(auth_headers):
    """RF-1: sin contacto -> 201 con nulls."""
    client = _make_app_and_client()
    resp = client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-002", "nombre": "Mayorista Norte"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert (
        data["email"] is None and data["telefono"] is None and data["direccion"] is None
    )


def test_post_duplicado_409(auth_headers):
    """RF-1: código duplicado (incluye normalizado e inactivo) -> 409."""
    client = _make_app_and_client()
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-003", "nombre": "Proveedor A"},
        headers=auth_headers,
    )
    resp = client.post(
        "/api/v1/proveedores",
        json={"codigo": "  prov-003 ", "nombre": "Proveedor B"},
        headers=auth_headers,
    )
    assert resp.status_code == 409
    assert "ya existe" in resp.json()["detail"].lower()


def test_post_validacion_422(auth_headers):
    """RF-1: validaciones Pydantic -> 422."""
    client = _make_app_and_client()
    # codigo corto
    resp = client.post(
        "/api/v1/proveedores",
        json={"codigo": "AB", "nombre": "Test"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    # nombre corto
    resp = client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-004", "nombre": "A"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    # email inválido
    resp = client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-005", "nombre": "Test", "email": "sinarroba"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    # telefono inválido
    resp = client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-006", "nombre": "Test", "telefono": "123456"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    # direccion corta
    resp = client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-007", "nombre": "Test", "direccion": "abcd"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    # codigo con espacio interno
    resp = client.post(
        "/api/v1/proveedores",
        json={"codigo": "PR 001", "nombre": "Test"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_post_sin_logica_en_router(auth_headers):
    """Principio 3: router delega a service, sin queries."""
    from pathlib import Path

    content = Path("app/routers/proveedores.py").read_text(encoding="utf-8")
    assert "proveedor_service" in content or "crear_proveedor" in content
    assert "SELECT" not in content
