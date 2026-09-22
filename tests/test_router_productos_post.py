"""Tests de T09 — Router POST /api/v1/productos (RF-1)."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from fastapi import FastAPI

# Importar modelos para registrar en Base
from app.models.producto import Producto  # noqa: F401
from app.models.movimiento_inventario import MovimientoInventario  # noqa: F401


def _make_app_and_client():
    """Crea app de test con DB en memoria y router de productos."""
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
    return client, engine


def test_post_crea_producto_201_normalizado(auth_headers):
    """RF-1: POST válido retorna 201 con sku normalizado y categoria normalizada."""
    client, _ = _make_app_and_client()
    resp = client.post(
        "/api/v1/productos",
        json={
            "sku": "  ps5-slim-001 ",
            "nombre": "PlayStation 5 Slim",
            "categoria": "  Consola ",
            "stock_inicial": 10,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["sku"] == "PS5-SLIM-001"
    assert data["categoria"] == "consola"
    assert data["nombre"] == "PlayStation 5 Slim"
    assert data["stock_inicial"] == 10
    assert data["estado"] == "activo"


def test_post_stock_omitido_default_0(auth_headers):
    """RF-1: stock omitido -> 201 con stock 0."""
    client, _ = _make_app_and_client()
    resp = client.post(
        "/api/v1/productos",
        json={"sku": "XBOX-001", "nombre": "Xbox Series X", "categoria": "consola"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["stock_inicial"] == 0


def test_post_duplicado_409(auth_headers):
    """RF-1: SKU duplicado (incluye normalizado) -> 409."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/productos",
        json={"sku": "DUPL-001", "nombre": "Producto A", "categoria": "videojuego"},
        headers=auth_headers,
    )
    resp = client.post(
        "/api/v1/productos",
        json={"sku": "  dupl-001 ", "nombre": "Producto B", "categoria": "consola"},
        headers=auth_headers,
    )
    assert resp.status_code == 409
    assert "ya existe" in resp.json()["detail"].lower()


def test_post_validacion_400_422(auth_headers):
    """RF-1: validaciones Pydantic -> 422."""
    client, _ = _make_app_and_client()
    # sku corto
    resp = client.post(
        "/api/v1/productos",
        json={"sku": "AB", "nombre": "Test", "categoria": "consola"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    # nombre corto
    resp = client.post(
        "/api/v1/productos",
        json={"sku": "SKU-002", "nombre": "A", "categoria": "consola"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    # categoria inválida
    resp = client.post(
        "/api/v1/productos",
        json={"sku": "SKU-003", "nombre": "Test", "categoria": "juego"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    # stock negativo
    resp = client.post(
        "/api/v1/productos",
        json={
            "sku": "SKU-004",
            "nombre": "Test",
            "categoria": "consola",
            "stock_inicial": -1,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422
    # stock decimal (string)
    resp = client.post(
        "/api/v1/productos",
        json={
            "sku": "SKU-005",
            "nombre": "Test",
            "categoria": "consola",
            "stock_inicial": "10",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_post_sin_logica_en_router(auth_headers):
    """Principio 3: router delega a service, sin queries directas."""
    from pathlib import Path

    router_path = Path("app/routers/productos.py")
    content = router_path.read_text(encoding="utf-8")
    # Router no debe contener lógica de negocio directa como queries o cálculo de stock
    assert "producto_service" in content or "crear_producto" in content
    assert "SELECT" not in content
    # No debe importar Base ni hacer queries directas
    assert "Base.metadata" not in content
