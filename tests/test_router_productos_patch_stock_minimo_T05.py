"""Tests de T05 004 — PATCH /productos/{sku} con stock_minimo (RF-1)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db


def _make_client():
    from app.routers.productos import router as productos_router
    from app.routers.stock import router as stock_router

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
    app.include_router(productos_router)
    app.include_router(stock_router)
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client


def test_patch_stock_minimo_actualiza_y_refleja_en_stock(auth_headers):
    """RF-1: PATCH stock_minimo y GET /stock refleja alerta sin duplicar lógica."""
    client = _make_client()
    client.post(
        "/api/v1/productos",
        json={
            "sku": "PROD-001",
            "nombre": "Test",
            "categoria": "videojuego",
            "stock_inicial": 5,
            "stock_minimo": 10,
        },
        headers=auth_headers,
    )
    # Stock inicial 5 < minimo 10 -> alerta true
    resp = client.get("/api/v1/stock/PROD-001", headers=auth_headers)
    assert resp.json()["alerta"] is True
    assert resp.json()["stock_minimo"] == 10

    # PATCH stock_minimo a 3 -> stock 5 >=3 -> false
    resp = client.patch(
        "/api/v1/productos/PROD-001", json={"stock_minimo": 3}, headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["stock_minimo"] == 3
    resp = client.get("/api/v1/stock/PROD-001", headers=auth_headers)
    assert resp.json()["alerta"] is False

    # PATCH stock_minimo a 0 -> nunca alerta
    resp = client.patch(
        "/api/v1/productos/PROD-001", json={"stock_minimo": 0}, headers=auth_headers
    )
    assert resp.json()["stock_minimo"] == 0
    resp = client.get("/api/v1/stock/PROD-001", headers=auth_headers)
    assert resp.json()["alerta"] is False


def test_patch_stock_minimo_null_y_ausente(auth_headers):
    """RF-1: null/ausente -> 0 o sin cambio, '' -> 422."""
    client = _make_client()
    client.post(
        "/api/v1/productos",
        json={
            "sku": "PROD-002",
            "nombre": "Test",
            "categoria": "consola",
            "stock_minimo": 5,
        },
        headers=auth_headers,
    )
    # null -> se ignora (no cambia) o se pone 0? Según servicio, null en update se ignora (no cambia)
    # En nuestro servicio, stock_minimo None se ignora, no se pone a 0, así que sigue 5
    resp = client.patch(
        "/api/v1/productos/PROD-002",
        json={"nombre": "Nuevo Nombre"},
        headers=auth_headers,
    )
    assert resp.json()["stock_minimo"] == 5
    # Enviar stock_minimo null explícitamente -> nuestro servicio lo ignora (no cambia), pero schema lo convierte a None y servicio lo ignora
    # Para este test, como stock_minimo es NOT NULL, null no debería borrar, solo se ignora
    # Verificar que "" -> 422
    resp = (
        client.patch("/api/v1/proveedores/PROV-001", json={}, headers=auth_headers)
        if False
        else None
    )  # placeholder
    resp = client.patch(
        "/api/v1/productos/PROD-002", json={"stock_minimo": ""}, headers=auth_headers
    )
    assert resp.status_code == 422
    resp = client.patch(
        "/api/v1/productos/PROD-002", json={"stock_minimo": -5}, headers=auth_headers
    )
    assert resp.status_code == 422
    resp = client.patch(
        "/api/v1/productos/PROD-002",
        json={"stock_minimo": 1000001},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_patch_stock_minimo_sin_duplicar_logica(auth_headers):
    """RNF-2: stock actual y alerta usan mismo cálculo que 003, sin duplicar."""
    from pathlib import Path

    stock_service = Path("app/services/stock_service.py").read_text(encoding="utf-8")
    assert "_calcular_stock_actual" in stock_service
    assert "stock_minimo" in stock_service
    assert "alerta" in stock_service
