"""Tests de T08 — Router GET /api/v1/proveedores listado (RF-2)."""

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


def test_get_proveedores_listado_vacio(auth_headers):
    """RF-2: sin proveedores -> []"""
    client, _ = _make_app_and_client()
    resp = client.get("/api/v1/proveedores", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json() == []


def test_get_proveedores_listado_solo_activos_ordenados(auth_headers):
    """RF-2: solo activos ordenados por codigo, sin estado, con email/telefono/direccion."""
    client, SessionLocal = _make_app_and_client()
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-002", "nombre": "Proveedor B", "email": "b@a.com"},
        headers=auth_headers,
    )
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-001", "nombre": "Proveedor A"},
        headers=auth_headers,
    )
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "PROV-003", "nombre": "Proveedor C"},
        headers=auth_headers,
    )
    db = SessionLocal()
    prov = db.query(Proveedor).filter(Proveedor.codigo == "PROV-003").first()
    prov.estado = "inactivo"
    db.commit()
    db.close()

    resp = client.get("/api/v1/proveedores", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert [item["codigo"] for item in data] == ["PROV-001", "PROV-002"]
    for item in data:
        assert "codigo" in item and "nombre" in item
        assert "estado" not in item  # sin estado en listado
        assert "email" in item


def test_get_proveedores_listado_delega_a_service(auth_headers):
    """Principio 3: router delega a service."""
    from pathlib import Path

    content = Path("app/routers/proveedores.py").read_text(encoding="utf-8")
    assert "listar_activos" in content
