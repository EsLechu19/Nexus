"""Tests de T09 — Router GET /api/v1/stock (RF-4)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.schemas.producto import ProductoCreate
from app.schemas.proveedor import ProveedorCreate


def _make_client_with_db():
    from app.routers.movimientos import router as mov_router
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
    app.include_router(mov_router)
    app.include_router(stock_router)
    # También necesitamos productos y proveedores para crear datos, pero los creamos vía service directo
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client, TestingSessionLocal


def _crear_datos(SessionLocal):
    from app.services.producto_service import crear_producto
    from app.services.proveedor_service import crear_proveedor

    db = SessionLocal()
    crear_producto(
        db,
        ProductoCreate(
            sku="PROD-001", nombre="Producto A", categoria="videojuego", stock_inicial=5
        ),
    )
    crear_producto(
        db,
        ProductoCreate(
            sku="PROD-002", nombre="Producto B", categoria="consola", stock_inicial=0
        ),
    )
    crear_proveedor(db, ProveedorCreate(codigo="PROV-001", nombre="Proveedor Test"))
    db.close()


def test_get_stock_por_codigo_activo_200(auth_headers):
    """RF-4: GET /stock/{codigo} activo -> 200 con stock_actual."""
    client, SessionLocal = _make_client_with_db()
    _crear_datos(SessionLocal)
    # Crear movimientos para PROD-001: entrada 10, salida 3
    client.post(
        "/api/v1/movimientos/entradas",
        json={
            "producto_codigo": "PROD-001",
            "proveedor_codigo": "PROV-001",
            "cantidad": 10,
        },
        headers=auth_headers,
    )
    client.post(
        "/api/v1/movimientos/salidas",
        json={"producto_codigo": "PROD-001", "cantidad": 3},
        headers=auth_headers,
    )

    resp = client.get("/api/v1/stock/PROD-001", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["codigo"] == "PROD-001"
    assert data["stock_inicial"] == 5
    assert data["entradas"] == 10
    assert data["salidas"] == 3
    assert data["stock_actual"] == 12  # 5+10-3


def test_get_stock_por_codigo_inactivo_200_trazabilidad(auth_headers):
    """RF-4: stock de inactivo -> 404 (solo lectura de activos, 004)."""
    client, SessionLocal = _make_client_with_db()
    _crear_datos(SessionLocal)
    db = SessionLocal()
    from app.models.producto import Producto

    prod = db.query(Producto).filter(Producto.sku == "PROD-001").first()
    prod.estado = "inactivo"
    db.commit()
    db.close()
    resp = client.get("/api/v1/stock/PROD-001", headers=auth_headers)
    assert resp.status_code == 404


def test_get_stock_por_codigo_no_existe_404(auth_headers):
    """RF-4: código inexistente -> 404."""
    client, _ = _make_client_with_db()
    resp = client.get("/api/v1/stock/NOPE", headers=auth_headers)
    assert resp.status_code == 404


def test_get_stock_por_codigo_normalizado(auth_headers):
    """RF-4: normaliza trim+upper."""
    client, SessionLocal = _make_client_with_db()
    _crear_datos(SessionLocal)
    resp = client.get("/api/v1/stock/  prod-001 ", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["codigo"] == "PROD-001"


def test_get_stock_global_solo_activos(auth_headers):
    """RF-4: GET /stock lista solo activos ordenados."""
    client, SessionLocal = _make_client_with_db()
    _crear_datos(SessionLocal)
    # Crear un inactivo
    db = SessionLocal()
    from app.models.producto import Producto

    p = db.query(Producto).filter(Producto.sku == "PROD-002").first()
    p.estado = "inactivo"
    db.commit()
    db.close()
    resp = client.get("/api/v1/stock", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["codigo"] == "PROD-001"
    # 004: global solo activos, sin flag incluir_inactivos
    resp = client.get(
        "/api/v1/stock", params={"incluir_inactivos": "true"}, headers=auth_headers
    )
    # Si se envía flag desconocido, se ignora y sigue devolviendo solo activos (o 422 según validación)
    # Para 004, incluir_inactivos no está soportado, así que debe seguir devolviendo solo activos
    assert resp.status_code in (200, 422)
    if resp.status_code == 200:
        assert len(resp.json()) == 1


def test_get_stock_sin_movimientos_igual_a_inicial(auth_headers):
    """RF-4: sin movimientos stock_actual == stock_inicial."""
    client, SessionLocal = _make_client_with_db()
    _crear_datos(SessionLocal)
    resp = client.get("/api/v1/stock/PROD-002", headers=auth_headers)
    assert resp.json()["stock_actual"] == 0
    assert resp.json()["stock_inicial"] == 0


def test_get_stock_delega_a_service(auth_headers):
    """Principio 3: router delega a service."""
    from pathlib import Path

    content = Path("app/routers/stock.py").read_text(encoding="utf-8")
    assert "calcular_stock" in content or "listar_stock" in content
