"""Tests de T08 — Router GET /api/v1/movimientos historial (RF-3)."""

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


def _crear_producto_proveedor(
    SessionLocal, prod_codigo="PROD-001", prov_codigo="PROV-001"
):
    from app.services.producto_service import crear_producto
    from app.services.proveedor_service import crear_proveedor

    db = SessionLocal()
    try:
        crear_producto(
            db,
            ProductoCreate(
                sku=prod_codigo,
                nombre="Producto Test",
                categoria="videojuego",
                stock_inicial=10,
            ),
        )
    except Exception:
        pass  # ya existe
    try:
        crear_proveedor(
            db, ProveedorCreate(codigo=prov_codigo, nombre="Proveedor Test")
        )
    except Exception:
        pass
    db.close()


def test_get_historial_vacio(auth_headers):
    """RF-3: sin movimientos -> []"""
    client, _ = _make_client_with_db()
    resp = client.get("/api/v1/movimientos", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json() == []


def test_get_historial_todos_orden_desc(auth_headers):
    """RF-3: sin filtros devuelve todos ordenados fecha DESC."""
    client, SessionLocal = _make_client_with_db()
    _crear_producto_proveedor(SessionLocal)
    # Crear otro producto para segundo movimiento
    db = SessionLocal()
    from app.services.producto_service import crear_producto

    try:
        crear_producto(
            db,
            ProductoCreate(
                sku="PROD-002",
                nombre="Otro Producto",
                categoria="consola",
                stock_inicial=0,
            ),
        )
    except Exception:
        pass
    db.close()

    client.post(
        "/api/v1/movimientos/entradas",
        json={
            "producto_codigo": "PROD-001",
            "proveedor_codigo": "PROV-001",
            "cantidad": 5,
        },
        headers=auth_headers,
    )
    client.post(
        "/api/v1/movimientos/salidas",
        json={"producto_codigo": "PROD-001", "cantidad": 2},
        headers=auth_headers,
    )
    client.post(
        "/api/v1/movimientos/entradas",
        json={
            "producto_codigo": "PROD-002",
            "proveedor_codigo": "PROV-001",
            "cantidad": 7,
        },
        headers=auth_headers,
    )

    resp = client.get("/api/v1/movimientos", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    # Incluye entrada_inicial de PROD-001 (stock_inicial 10) + 3 movimientos = 4
    assert len(data) == 4
    # Orden DESC: último creado primero
    assert data[0]["cantidad"] == 7 and data[0]["producto_codigo"] == "PROD-002"


def test_get_historial_filtro_producto(auth_headers):
    """RF-3: filtro por producto normalizado."""
    client, SessionLocal = _make_client_with_db()
    _crear_producto_proveedor(SessionLocal)
    db = SessionLocal()
    from app.services.producto_service import crear_producto

    try:
        crear_producto(
            db,
            ProductoCreate(
                sku="PROD-002", nombre="Otro", categoria="videojuego", stock_inicial=0
            ),
        )
    except Exception:
        pass
    db.close()
    client.post(
        "/api/v1/movimientos/entradas",
        json={
            "producto_codigo": "PROD-001",
            "proveedor_codigo": "PROV-001",
            "cantidad": 5,
        },
        headers=auth_headers,
    )
    client.post(
        "/api/v1/movimientos/entradas",
        json={
            "producto_codigo": "PROD-002",
            "proveedor_codigo": "PROV-001",
            "cantidad": 7,
        },
        headers=auth_headers,
    )

    resp = client.get(
        "/api/v1/movimientos",
        params={"producto_codigo": "PROD-001"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    # Incluye entrada_inicial + entrada 5 = 2
    assert len(resp.json()) == 2
    assert all(m["producto_codigo"] == "PROD-001" for m in resp.json())

    # Normalizado
    resp = client.get(
        "/api/v1/movimientos",
        params={"producto_codigo": "  prod-001 "},
        headers=auth_headers,
    )
    assert len(resp.json()) == 2

    # Producto inexistente -> 404
    resp = client.get(
        "/api/v1/movimientos", params={"producto_codigo": "NOPE"}, headers=auth_headers
    )
    assert resp.status_code == 404


def test_get_historial_filtro_tipo(auth_headers):
    """RF-3: filtro por tipo entrada/salida."""
    client, SessionLocal = _make_client_with_db()
    _crear_producto_proveedor(SessionLocal)
    client.post(
        "/api/v1/movimientos/entradas",
        json={
            "producto_codigo": "PROD-001",
            "proveedor_codigo": "PROV-001",
            "cantidad": 5,
        },
        headers=auth_headers,
    )
    client.post(
        "/api/v1/movimientos/salidas",
        json={"producto_codigo": "PROD-001", "cantidad": 2},
        headers=auth_headers,
    )

    resp = client.get(
        "/api/v1/movimientos", params={"tipo": "entrada"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert all(m["tipo"] == "entrada" for m in resp.json())
    assert len(resp.json()) == 1

    resp = client.get(
        "/api/v1/movimientos", params={"tipo": "salida"}, headers=auth_headers
    )
    assert len(resp.json()) == 1
    assert resp.json()[0]["tipo"] == "salida"

    # Tipo inválido -> 422
    resp = client.get(
        "/api/v1/movimientos", params={"tipo": "invalido"}, headers=auth_headers
    )
    assert resp.status_code == 422


def test_get_historial_filtro_ambos(auth_headers):
    """RF-3: filtros combinados."""
    client, SessionLocal = _make_client_with_db()
    _crear_producto_proveedor(SessionLocal)
    client.post(
        "/api/v1/movimientos/entradas",
        json={
            "producto_codigo": "PROD-001",
            "proveedor_codigo": "PROV-001",
            "cantidad": 5,
        },
        headers=auth_headers,
    )
    client.post(
        "/api/v1/movimientos/salidas",
        json={"producto_codigo": "PROD-001", "cantidad": 2},
        headers=auth_headers,
    )

    resp = client.get(
        "/api/v1/movimientos",
        params={"producto_codigo": "PROD-001", "tipo": "entrada"},
        headers=auth_headers,
    )
    assert len(resp.json()) == 1
    assert resp.json()[0]["tipo"] == "entrada"


def test_get_historial_delega_a_service(auth_headers):
    """Principio 3: router delega a service."""
    from pathlib import Path

    content = Path("app/routers/movimientos.py").read_text(encoding="utf-8")
    assert "listar_historial" in content
