"""Tests de T09 — Router GET /api/v1/proveedores/{codigo} detalle (RF-3)."""

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


def test_get_detalle_activo_200(auth_headers):
    """RF-3: detalle activo retorna 200 con estado."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/proveedores",
        json={
            "codigo": "PROV-010",
            "nombre": "Central Distribuidora",
            "email": "a@b.com",
        },
        headers=auth_headers,
    )
    resp = client.get("/api/v1/proveedores/PROV-010", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["codigo"] == "PROV-010"
    assert data["nombre"] == "Central Distribuidora"
    assert data["estado"] == "activo"
    assert "email" in data


def test_get_detalle_inactivo_200_trazabilidad(auth_headers):
    """RF-3: detalle inactivo también 200."""
    client, SessionLocal = _make_app_and_client()
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-011", "nombre": "Baja Proveedor"},
        headers=auth_headers,
    )
    db = SessionLocal()
    prov = db.query(Proveedor).filter(Proveedor.codigo == "PROV-011").first()
    prov.estado = "inactivo"
    db.commit()
    db.close()

    resp = client.get("/api/v1/proveedores/PROV-011", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["estado"] == "inactivo"


def test_get_detalle_normalizado(auth_headers):
    """RF-3: código normalizado trim+upper."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-012", "nombre": "Test Proveedor"},
        headers=auth_headers,
    )
    resp = client.get("/api/v1/proveedores/  prov-012 ", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["codigo"] == "PROV-012"


def test_get_detalle_no_existe_404(auth_headers):
    """RF-3: no existe -> 404."""
    client, _ = _make_app_and_client()
    resp = client.get("/api/v1/proveedores/NO-EXISTE", headers=auth_headers)
    assert resp.status_code == 404
    assert "no encontrado" in resp.json()["detail"].lower()


def test_get_detalle_delega_a_service(auth_headers):
    """Principio 3: router delega a service."""
    from pathlib import Path

    content = Path("app/routers/proveedores.py").read_text(encoding="utf-8")
    assert "obtener_por_codigo" in content
