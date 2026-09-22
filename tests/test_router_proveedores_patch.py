"""Tests de T10 — Router PATCH /api/v1/proveedores/{codigo} edición (RF-4)."""

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
    return client, TestingSessionLocal


def test_patch_edita_nombre_200(auth_headers):
    """RF-4: PATCH solo nombre -> 200."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-020", "nombre": "Original Nombre"},
        headers=auth_headers,
    )
    resp = client.patch(
        "/api/v1/proveedores/PROV-020",
        json={"nombre": "Nuevo Nombre"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["nombre"] == "Nuevo Nombre"
    assert resp.json()["codigo"] == "PROV-020"


def test_patch_edita_contacto_200(auth_headers):
    """RF-4: PATCH email/telefono/direccion -> 200."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-021", "nombre": "Test Proveedor"},
        headers=auth_headers,
    )
    resp = client.patch(
        "/api/v1/proveedores/PROV-021",
        json={"email": "nuevo@a.com", "telefono": "+34 600 123 456"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "nuevo@a.com"
    assert resp.json()["telefono"] == "+34 600 123 456"


def test_patch_null_borra_200(auth_headers):
    """RF-4: null borra campo -> 200 y null."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-022", "nombre": "Test", "email": "old@a.com"},
        headers=auth_headers,
    )
    resp = client.patch(
        "/api/v1/proveedores/PROV-022", json={"email": None}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["email"] is None


def test_patch_codigo_mismo_se_ignora_200(auth_headers):
    """RF-4: codigo mismo se ignora -> 200."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-023", "nombre": "Test Proveedor"},
        headers=auth_headers,
    )
    resp = client.patch(
        "/api/v1/proveedores/PROV-023",
        json={"nombre": "Cambiado", "codigo": "  prov-023 "},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Cambiado"


def test_patch_codigo_distinto_400(auth_headers):
    """RF-4: codigo distinto -> 400 inmutable."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-024", "nombre": "Test Proveedor"},
        headers=auth_headers,
    )
    resp = client.patch(
        "/api/v1/proveedores/PROV-024",
        json={"nombre": "Nuevo", "codigo": "OTRO-999"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "inmutable" in resp.json()["detail"].lower()


def test_patch_inactivo_400(auth_headers):
    """RF-4: inactivo no editable -> 400."""
    client, SessionLocal = _make_app_and_client()
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-025", "nombre": "Test Proveedor"},
        headers=auth_headers,
    )
    db = SessionLocal()
    prov = db.query(Proveedor).filter(Proveedor.codigo == "PROV-025").first()
    prov.estado = "inactivo"
    db.commit()
    db.close()
    resp = client.patch(
        "/api/v1/proveedores/PROV-025", json={"nombre": "Nuevo"}, headers=auth_headers
    )
    assert resp.status_code == 400


def test_patch_no_encontrado_404(auth_headers):
    """RF-4: no existe -> 404."""
    client, _ = _make_app_and_client()
    resp = client.patch(
        "/api/v1/proveedores/NO-EXISTE", json={"nombre": "Nuevo"}, headers=auth_headers
    )
    assert resp.status_code == 404


def test_patch_payload_vacio_422(auth_headers):
    """RF-4: payload vacío -> 422."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-026", "nombre": "Test Proveedor"},
        headers=auth_headers,
    )
    resp = client.patch("/api/v1/proveedores/PROV-026", json={}, headers=auth_headers)
    assert resp.status_code == 422


def test_patch_validacion_422(auth_headers):
    """RF-4: validación Pydantic -> 422."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-027", "nombre": "Test Proveedor"},
        headers=auth_headers,
    )
    resp = client.patch(
        "/api/v1/proveedores/PROV-027", json={"nombre": "A"}, headers=auth_headers
    )
    assert resp.status_code == 422
    resp = client.patch(
        "/api/v1/proveedores/PROV-027",
        json={"email": "sinarroba"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    resp = client.patch(
        "/api/v1/proveedores/PROV-027", json={"telefono": "123"}, headers=auth_headers
    )
    assert resp.status_code == 422
    resp = client.patch(
        "/api/v1/proveedores/PROV-027", json={"direccion": "ab"}, headers=auth_headers
    )
    assert resp.status_code == 422


def test_patch_delega_a_service(auth_headers):
    """Principio 3: router delega a service."""
    from pathlib import Path

    content = Path("app/routers/proveedores.py").read_text(encoding="utf-8")
    assert "actualizar_proveedor" in content
