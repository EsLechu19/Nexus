"""Tests de T11 — Router DELETE /api/v1/proveedores/{codigo} baja lógica (RF-5)."""

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


def test_delete_baja_activo_200(auth_headers):
    """RF-5: DELETE activo -> 200 inactivo."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-030", "nombre": "Test Proveedor"},
        headers=auth_headers,
    )
    resp = client.delete("/api/v1/proveedores/PROV-030", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["estado"] == "inactivo"
    assert resp.json()["codigo"] == "PROV-030"


def test_delete_ya_inactivo_400(auth_headers):
    """RF-5: ya inactivo -> 400."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-031", "nombre": "Test Proveedor"},
        headers=auth_headers,
    )
    client.delete("/api/v1/proveedores/PROV-031", headers=auth_headers)
    resp = client.delete("/api/v1/proveedores/PROV-031", headers=auth_headers)
    assert resp.status_code == 400
    assert (
        "ya" in resp.json()["detail"].lower() or "baja" in resp.json()["detail"].lower()
    )


def test_delete_no_existe_404(auth_headers):
    """RF-5: no existe -> 404."""
    client, _ = _make_app_and_client()
    resp = client.delete("/api/v1/proveedores/NO-EXISTE", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_normaliza_codigo_path(auth_headers):
    """RF-5: normaliza trim+upper."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-032", "nombre": "Test Proveedor"},
        headers=auth_headers,
    )
    resp = client.delete("/api/v1/proveedores/  prov-032 ", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["estado"] == "inactivo"


def test_delete_excluido_de_listado_pero_visible_en_detalle(auth_headers):
    """RF-5: tras baja, excluido de listado pero visible en detalle."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-033", "nombre": "Visible"},
        headers=auth_headers,
    )
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-034", "nombre": "Otro"},
        headers=auth_headers,
    )
    client.delete("/api/v1/proveedores/PROV-033", headers=auth_headers)

    resp = client.get("/api/v1/proveedores", headers=auth_headers)
    skus = {item["codigo"] for item in resp.json()}
    assert "PROV-033" not in skus
    assert "PROV-034" in skus

    resp = client.get("/api/v1/proveedores/PROV-033", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["estado"] == "inactivo"


def test_delete_delega_a_service(auth_headers):
    """Principio 3: router delega a service."""
    from pathlib import Path

    content = Path("app/routers/proveedores.py").read_text(encoding="utf-8")
    assert "baja_proveedor" in content
