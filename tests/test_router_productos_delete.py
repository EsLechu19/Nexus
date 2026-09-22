"""Tests de T13 — Router DELETE /api/v1/productos/{sku} baja lógica (RF-5)."""

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


def test_delete_baja_activo_200(auth_headers):
    """RF-5: DELETE activo -> 200 con estado inactivo."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/productos",
        json={"sku": "SKU-030", "nombre": "Test", "categoria": "videojuego"},
        headers=auth_headers,
    )
    resp = client.delete("/api/v1/productos/SKU-030", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["sku"] == "SKU-030"
    assert data["estado"] == "inactivo"


def test_delete_con_stock_permite_200(auth_headers):
    """RF-5: permite baja con cualquier stock_inicial."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/productos",
        json={
            "sku": "SKU-031",
            "nombre": "Test",
            "categoria": "consola",
            "stock_inicial": 50,
        },
        headers=auth_headers,
    )
    resp = client.delete("/api/v1/productos/SKU-031", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["stock_inicial"] == 50


def test_delete_ya_inactivo_400(auth_headers):
    """RF-5: ya inactivo -> 400."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/productos",
        json={"sku": "SKU-032", "nombre": "Test", "categoria": "videojuego"},
        headers=auth_headers,
    )
    client.delete("/api/v1/productos/SKU-032", headers=auth_headers)
    resp = client.delete("/api/v1/productos/SKU-032", headers=auth_headers)
    assert resp.status_code == 400
    assert (
        "ya" in resp.json()["detail"].lower() or "baja" in resp.json()["detail"].lower()
    )


def test_delete_no_existe_404(auth_headers):
    """RF-5: SKU inexistente -> 404."""
    client, _ = _make_app_and_client()
    resp = client.delete("/api/v1/productos/NO-EXISTE", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_normaliza_sku_path(auth_headers):
    """RF-5: SKU path normalizado trim+upper."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/productos",
        json={"sku": "SKU-033", "nombre": "Test", "categoria": "accesorio"},
        headers=auth_headers,
    )
    resp = client.delete("/api/v1/productos/  sku-033 ", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["estado"] == "inactivo"


def test_delete_excluido_de_listado_pero_visible_en_detalle(auth_headers):
    """RF-5: tras baja, excluido de listado pero visible en detalle."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/productos",
        json={"sku": "SKU-034", "nombre": "Visible", "categoria": "consola"},
        headers=auth_headers,
    )
    client.post(
        "/api/v1/productos",
        json={"sku": "SKU-035", "nombre": "Otro", "categoria": "videojuego"},
        headers=auth_headers,
    )
    client.delete("/api/v1/productos/SKU-034", headers=auth_headers)

    # listado excluye inactivo
    resp = client.get("/api/v1/productos", headers=auth_headers)
    skus = {item["sku"] for item in resp.json()}
    assert "SKU-034" not in skus
    assert "SKU-035" in skus

    # detalle incluye inactivo
    resp = client.get("/api/v1/productos/SKU-034", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["estado"] == "inactivo"


def test_delete_delega_a_service(auth_headers):
    """Principio 3: router delega a service."""
    from pathlib import Path

    content = Path("app/routers/productos.py").read_text(encoding="utf-8")
    assert "baja_producto" in content
