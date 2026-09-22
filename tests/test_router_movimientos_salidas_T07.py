"""Tests de T07 — Router POST /api/v1/movimientos/salidas (RF-2)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.schemas.producto import ProductoCreate
from app.schemas.proveedor import ProveedorCreate


def _make_client_with_db():
    from app.routers.movimientos import router

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


def _crear_producto_proveedor(SessionLocal):
    from app.services.producto_service import crear_producto
    from app.services.proveedor_service import crear_proveedor

    db = SessionLocal()
    crear_producto(
        db,
        ProductoCreate(
            sku="PROD-001",
            nombre="Producto Test",
            categoria="videojuego",
            stock_inicial=10,
        ),
    )
    crear_proveedor(db, ProveedorCreate(codigo="PROV-001", nombre="Proveedor Test"))
    db.close()


def test_post_salida_valida_201(auth_headers):
    """RF-2: POST salida válida -> 201 con stock_actual decrementado."""
    client, SessionLocal = _make_client_with_db()
    _crear_producto_proveedor(SessionLocal)
    # Crear entrada previa para tener stock 15
    client.post(
        "/api/v1/movimientos/entradas",
        json={
            "producto_codigo": "PROD-001",
            "proveedor_codigo": "PROV-001",
            "cantidad": 5,
        },
        headers=auth_headers,
    )
    resp = client.post(
        "/api/v1/movimientos/salidas",
        json={"producto_codigo": "PROD-001", "cantidad": 8, "motivo": "Venta"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["tipo"] == "salida"
    assert data["proveedor_codigo"] is None
    assert data["cantidad"] == 8
    assert data["stock_actual"] == 7  # 10 inicial +5 -8 =7
    assert "id" in data and "fecha" in data


def test_post_salida_exacta_deja_cero_201(auth_headers):
    """RF-2: salida exacta deja 0."""
    client, SessionLocal = _make_client_with_db()
    _crear_producto_proveedor(SessionLocal)
    resp = client.post(
        "/api/v1/movimientos/salidas",
        json={"producto_codigo": "PROD-001", "cantidad": 10},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["stock_actual"] == 0


def test_post_salida_stock_insuficiente_400(auth_headers):
    """RF-2: stock insuficiente -> 400 sin movimiento."""
    client, SessionLocal = _make_client_with_db()
    _crear_producto_proveedor(SessionLocal)
    resp = client.post(
        "/api/v1/movimientos/salidas",
        json={"producto_codigo": "PROD-001", "cantidad": 11},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "stock" in resp.json()["detail"].lower()


def test_post_salida_producto_no_existe_404(auth_headers):
    client, SessionLocal = _make_client_with_db()
    _crear_producto_proveedor(SessionLocal)
    resp = client.post(
        "/api/v1/movimientos/salidas",
        json={"producto_codigo": "NOPE", "cantidad": 1},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_post_salida_producto_inactivo_400(auth_headers):
    client, SessionLocal = _make_client_with_db()
    _crear_producto_proveedor(SessionLocal)
    db = SessionLocal()
    from app.models.producto import Producto

    prod = db.query(Producto).filter(Producto.sku == "PROD-001").first()
    prod.estado = "inactivo"
    db.commit()
    db.close()
    resp = client.post(
        "/api/v1/movimientos/salidas",
        json={"producto_codigo": "PROD-001", "cantidad": 1},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_post_salida_proveedor_enviado_422(auth_headers):
    """RF-2: salida no debe llevar proveedor -> 422."""
    client, SessionLocal = _make_client_with_db()
    _crear_producto_proveedor(SessionLocal)
    resp = client.post(
        "/api/v1/movimientos/salidas",
        json={
            "producto_codigo": "PROD-001",
            "cantidad": 1,
            "proveedor_codigo": "PROV-001",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_post_salida_validacion_422(auth_headers):
    client, SessionLocal = _make_client_with_db()
    _crear_producto_proveedor(SessionLocal)
    assert (
        client.post(
            "/api/v1/movimientos/salidas",
            json={"producto_codigo": "PROD-001", "cantidad": 0},
            headers=auth_headers,
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/movimientos/salidas",
            json={"producto_codigo": "PROD-001", "cantidad": 1, "motivo": ""},
            headers=auth_headers,
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/movimientos/salidas",
            json={"producto_codigo": "AB", "cantidad": 1},
            headers=auth_headers,
        ).status_code
        == 422
    )


def test_post_salida_normaliza_codigo_201(auth_headers):
    client, SessionLocal = _make_client_with_db()
    _crear_producto_proveedor(SessionLocal)
    resp = client.post(
        "/api/v1/movimientos/salidas",
        json={"producto_codigo": "  prod-001 ", "cantidad": 1},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["producto_codigo"] == "PROD-001"


def test_post_salida_delega_a_service(auth_headers):
    from pathlib import Path

    content = Path("app/routers/movimientos.py").read_text(encoding="utf-8")
    assert "registrar_salida" in content
