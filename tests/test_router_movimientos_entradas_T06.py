"""Tests de T06 — Router POST /api/v1/movimientos/entradas (RF-1)."""

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
    return client, TestingSessionLocal, engine


def _crear_producto_y_proveedor(SessionLocal):
    from app.services.producto_service import crear_producto
    from app.services.proveedor_service import crear_proveedor

    db = SessionLocal()
    crear_producto(
        db,
        ProductoCreate(
            sku="PROD-001",
            nombre="Producto Test",
            categoria="videojuego",
            stock_inicial=5,
        ),
    )
    crear_proveedor(db, ProveedorCreate(codigo="PROV-001", nombre="Proveedor Test"))
    db.close()


def test_post_entrada_valida_201(auth_headers):
    """RF-1: POST entrada válida -> 201 con stock_actual."""
    client, SessionLocal, _ = _make_client_with_db()
    _crear_producto_y_proveedor(SessionLocal)
    resp = client.post(
        "/api/v1/movimientos/entradas",
        json={
            "producto_codigo": "PROD-001",
            "proveedor_codigo": "PROV-001",
            "cantidad": 10,
            "motivo": "Compra semanal",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["producto_codigo"] == "PROD-001"
    assert data["proveedor_codigo"] == "PROV-001"
    assert data["tipo"] == "entrada"
    assert data["cantidad"] == 10
    assert data["stock_actual"] == 15
    assert "id" in data and "fecha" in data


def test_post_entrada_sin_motivo_201(auth_headers):
    """RF-1: motivo null/ausente -> 201."""
    client, SessionLocal, _ = _make_client_with_db()
    _crear_producto_y_proveedor(SessionLocal)
    resp = client.post(
        "/api/v1/movimientos/entradas",
        json={
            "producto_codigo": "PROD-001",
            "proveedor_codigo": "PROV-001",
            "cantidad": 5,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["motivo"] is None


def test_post_entrada_producto_no_existe_404(auth_headers):
    """RF-1: producto no existe -> 404."""
    client, SessionLocal, _ = _make_client_with_db()
    _crear_producto_y_proveedor(SessionLocal)
    resp = client.post(
        "/api/v1/movimientos/entradas",
        json={"producto_codigo": "NOPE", "proveedor_codigo": "PROV-001", "cantidad": 1},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_post_entrada_proveedor_no_existe_404(auth_headers):
    """RF-1: proveedor no existe -> 404."""
    client, SessionLocal, _ = _make_client_with_db()
    _crear_producto_y_proveedor(SessionLocal)
    resp = client.post(
        "/api/v1/movimientos/entradas",
        json={"producto_codigo": "PROD-001", "proveedor_codigo": "NOPE", "cantidad": 1},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_post_entrada_proveedor_inactivo_400(auth_headers):
    """RF-1: proveedor inactivo -> 400."""
    client, SessionLocal, _ = _make_client_with_db()
    _crear_producto_y_proveedor(SessionLocal)
    db = SessionLocal()
    from app.models.proveedor import Proveedor

    prov = db.query(Proveedor).filter(Proveedor.codigo == "PROV-001").first()
    prov.estado = "inactivo"
    db.commit()
    db.close()
    resp = client.post(
        "/api/v1/movimientos/entradas",
        json={
            "producto_codigo": "PROD-001",
            "proveedor_codigo": "PROV-001",
            "cantidad": 1,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_post_entrada_producto_inactivo_400(auth_headers):
    """RF-1: producto inactivo -> 400."""
    client, SessionLocal, _ = _make_client_with_db()
    _crear_producto_y_proveedor(SessionLocal)
    db = SessionLocal()
    from app.models.producto import Producto

    prod = db.query(Producto).filter(Producto.sku == "PROD-001").first()
    prod.estado = "inactivo"
    db.commit()
    db.close()
    resp = client.post(
        "/api/v1/movimientos/entradas",
        json={
            "producto_codigo": "PROD-001",
            "proveedor_codigo": "PROV-001",
            "cantidad": 1,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_post_entrada_validacion_422(auth_headers):
    """RF-1: validación Pydantic -> 422."""
    client, SessionLocal, _ = _make_client_with_db()
    _crear_producto_y_proveedor(SessionLocal)
    # cantidad 0
    assert (
        client.post(
            "/api/v1/movimientos/entradas",
            json={
                "producto_codigo": "PROD-001",
                "proveedor_codigo": "PROV-001",
                "cantidad": 0,
            },
            headers=auth_headers,
        ).status_code
        == 422
    )
    # motivo ""
    assert (
        client.post(
            "/api/v1/movimientos/entradas",
            json={
                "producto_codigo": "PROD-001",
                "proveedor_codigo": "PROV-001",
                "cantidad": 1,
                "motivo": "",
            },
            headers=auth_headers,
        ).status_code
        == 422
    )
    # proveedor_codigo missing
    assert (
        client.post(
            "/api/v1/movimientos/entradas",
            json={"producto_codigo": "PROD-001", "cantidad": 1},
            headers=auth_headers,
        ).status_code
        == 422
    )


def test_post_entrada_delega_a_service(auth_headers):
    """Principio 3: router delega a service."""
    from pathlib import Path

    content = Path("app/routers/movimientos.py").read_text(encoding="utf-8")
    assert "registrar_entrada" in content
