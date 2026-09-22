"""Tests de T11 — Router GET /api/v1/productos/{sku} detalle (RF-3)."""

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


def test_get_detalle_activo_200(auth_headers):
    """RF-3: detalle activo retorna 200 con sku, nombre, categoria, stock_inicial, estado."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/productos",
        json={
            "sku": "SKU-010",
            "nombre": "Zelda",
            "categoria": "videojuego",
            "stock_inicial": 7,
        },
        headers=auth_headers,
    )
    resp = client.get("/api/v1/productos/SKU-010", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["sku"] == "SKU-010"
    assert data["nombre"] == "Zelda"
    assert data["categoria"] == "videojuego"
    assert data["stock_inicial"] == 7
    assert data["estado"] == "activo"


def test_get_detalle_inactivo_200_trazabilidad(auth_headers):
    """RF-3: detalle inactivo también 200 (trazabilidad)."""
    client, SessionLocal = _make_app_and_client()
    client.post(
        "/api/v1/productos",
        json={"sku": "SKU-011", "nombre": "Baja", "categoria": "consola"},
        headers=auth_headers,
    )
    db = SessionLocal()
    prod = db.query(Producto).filter(Producto.sku == "SKU-011").first()
    prod.estado = "inactivo"
    db.commit()
    db.close()

    resp = client.get("/api/v1/productos/SKU-011", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["estado"] == "inactivo"


def test_get_detalle_normalizado(auth_headers):
    """RF-3: SKU normalizado trim+upper en path."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/productos",
        json={"sku": "SKU-012", "nombre": "Test", "categoria": "accesorio"},
        headers=auth_headers,
    )
    resp = client.get("/api/v1/productos/  sku-012 ", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["sku"] == "SKU-012"


def test_get_detalle_no_existe_404(auth_headers):
    """RF-3: SKU inexistente -> 404."""
    client, _ = _make_app_and_client()
    resp = client.get("/api/v1/productos/NO-EXISTE", headers=auth_headers)
    assert resp.status_code == 404
    assert "no encontrado" in resp.json()["detail"].lower()


def test_get_detalle_delega_a_service(auth_headers):
    """Principio 3: router delega a service."""
    from pathlib import Path

    content = Path("app/routers/productos.py").read_text(encoding="utf-8")
    assert "obtener_por_sku" in content
