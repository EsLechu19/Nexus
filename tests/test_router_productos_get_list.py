"""Tests de T10 — Router GET /api/v1/productos listado (RF-2)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models.movimiento_inventario import MovimientoInventario  # noqa: F401
from app.models.producto import Producto  # noqa: F401


def _make_app_and_client():
    from app.routers.productos import router

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


def test_get_listado_vacio(auth_headers):
    """RF-2: sin productos -> []"""
    client, _ = _make_app_and_client()
    resp = client.get("/api/v1/productos", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json() == []


def test_get_listado_solo_activos(auth_headers):
    """RF-2: devuelve solo activos con sku, nombre, categoria, stock_inicial."""
    client, SessionLocal = _make_app_and_client()
    # Crear 2 activos y 1 inactivo vía POST
    client.post(
        "/api/v1/productos",
        json={
            "sku": "SKU-001",
            "nombre": "Juego A",
            "categoria": "videojuego",
            "stock_inicial": 5,
        },
        headers=auth_headers,
    )
    client.post(
        "/api/v1/productos",
        json={
            "sku": "SKU-002",
            "nombre": "Consola B",
            "categoria": "consola",
            "stock_inicial": 0,
        },
        headers=auth_headers,
    )
    client.post(
        "/api/v1/productos",
        json={"sku": "SKU-003", "nombre": "Accesorio C", "categoria": "accesorio"},
        headers=auth_headers,
    )
    # Dar de baja SKU-003 directamente en DB
    db = SessionLocal()
    prod = db.query(Producto).filter(Producto.sku == "SKU-003").first()
    prod.estado = "inactivo"
    db.commit()
    db.close()

    resp = client.get("/api/v1/productos", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    skus = {item["sku"] for item in data}
    assert skus == {"SKU-001", "SKU-002"}
    for item in data:
        assert (
            "sku" in item
            and "nombre" in item
            and "categoria" in item
            and "stock_inicial" in item
        )
        # No debe incluir inactivo
        assert item["sku"] != "SKU-003"


def test_get_listado_delega_a_service(auth_headers):
    """Principio 3: router delega a service, sin queries directas."""
    from pathlib import Path

    content = Path("app/routers/productos.py").read_text(encoding="utf-8")
    assert "listar_activos" in content
    assert "SELECT" not in content
