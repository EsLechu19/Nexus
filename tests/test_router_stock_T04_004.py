"""Tests de T04 004 — Router GET /stock con alerta (RF-1)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.schemas.producto import ProductoCreate


def _make_client_with_db():
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
    app.include_router(stock_router)
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client, TestingSessionLocal


def _crear_producto(SessionLocal, codigo="PROD-001", stock_inicial=5, stock_minimo=10):
    from app.services.producto_service import crear_producto

    db = SessionLocal()
    prod = crear_producto(
        db,
        ProductoCreate(
            sku=codigo,
            nombre="Producto Test",
            categoria="videojuego",
            stock_inicial=stock_inicial,
            stock_minimo=stock_minimo,
        ),
    )
    db.close()
    return prod


def test_get_stock_con_alerta_true(auth_headers):
    """RF-1: stock_actual 5 < minimo 10 -> true."""
    client, SessionLocal = _make_client_with_db()
    _crear_producto(SessionLocal, codigo="PROD-001", stock_inicial=5, stock_minimo=10)
    resp = client.get("/api/v1/stock/PROD-001", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["codigo"] == "PROD-001"
    assert data["stock_minimo"] == 10
    assert data["stock_actual"] == 5
    assert data["alerta"] is True


def test_get_stock_con_alerta_false(auth_headers):
    """RF-1: stock_actual >= minimo -> false, y minimo 0 -> false."""
    client, SessionLocal = _make_client_with_db()
    _crear_producto(SessionLocal, codigo="PROD-002", stock_inicial=10, stock_minimo=10)
    assert (
        client.get("/api/v1/stock/PROD-002", headers=auth_headers).json()["alerta"]
        is False
    )
    _crear_producto(SessionLocal, codigo="PROD-003", stock_inicial=0, stock_minimo=0)
    assert (
        client.get("/api/v1/stock/PROD-003", headers=auth_headers).json()["alerta"]
        is False
    )


def test_get_stock_listado_solo_activos_con_alerta(auth_headers):
    """RF-1: listado solo activos ordenados, con alerta."""
    client, SessionLocal = _make_client_with_db()
    _crear_producto(SessionLocal, codigo="PROD-010", stock_inicial=2, stock_minimo=5)
    _crear_producto(SessionLocal, codigo="PROD-002", stock_inicial=10, stock_minimo=5)
    _crear_producto(SessionLocal, codigo="PROD-003", stock_inicial=5, stock_minimo=10)
    # Inactivar PROD-003
    from app.models.producto import Producto

    db = SessionLocal()
    prod = db.query(Producto).filter(Producto.sku == "PROD-003").first()
    prod.estado = "inactivo"
    db.commit()
    db.close()

    resp = client.get("/api/v1/stock", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    codigos = [d["codigo"] for d in data]
    assert "PROD-003" not in codigos
    assert codigos == sorted(codigos)
    for item in data:
        assert "alerta" in item and "stock_minimo" in item


def test_get_stock_no_existe_404_y_inactivo_404(auth_headers):
    """RF-1: no existe 404, inactivo 404."""
    client, SessionLocal = _make_client_with_db()
    _crear_producto(SessionLocal, codigo="PROD-004", stock_inicial=5, stock_minimo=10)
    assert client.get("/api/v1/stock/NOPE", headers=auth_headers).status_code == 404
    db = SessionLocal()
    from app.models.producto import Producto

    prod = db.query(Producto).filter(Producto.sku == "PROD-004").first()
    prod.estado = "inactivo"
    db.commit()
    db.close()
    assert client.get("/api/v1/stock/PROD-004", headers=auth_headers).status_code == 404


def test_get_stock_codigo_invalido_422(auth_headers):
    """RF-1: codigo formato inválido -> 422."""
    client, _ = _make_client_with_db()
    assert client.get("/api/v1/stock/AB", headers=auth_headers).status_code == 422


def test_get_stock_delega_a_service(auth_headers):
    """Principio 3: router delega a service."""
    from pathlib import Path

    content = Path("app/routers/stock.py").read_text(encoding="utf-8")
    assert "stock_service" in content
