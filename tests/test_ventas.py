"""Tests de T09 — Integración ventas con Bearer (RF-1..RF-4, RNF-5) — TDD."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models.movimiento_inventario  # noqa: F401
import app.models.producto  # noqa: F401
import app.models.proveedor  # noqa: F401
import app.models.usuario  # noqa: F401
import app.models.venta  # noqa: F401
import app.models.venta_item  # noqa: F401
from app.database import Base, get_db
from app.models.producto import Producto


def _make_client():
    from app.main import app

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

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client, TestingSessionLocal


def _setup_productos(client, SessionLocal, headers):
    # helper no usado directamente, productos se crean vía DB para simplificar
    pass


def test_ventas_post_201_con_2_ids(auth_headers):
    """T09: POST /ventas 201 con created_at Z y movimientos_ids 2 IDs."""
    client, SessionLocal = _make_client()
    db = SessionLocal()
    p1 = Producto(
        sku="PROD-001",
        nombre="Producto A",
        categoria="consola",
        stock_inicial=10,
        estado="activo",
    )
    p2 = Producto(
        sku="PROD-002",
        nombre="Producto B",
        categoria="consola",
        stock_inicial=10,
        estado="activo",
    )
    db.add_all([p1, p2])
    db.commit()
    db.close()

    resp = client.post(
        "/api/v1/ventas",
        json={
            "cliente": {"nombre": "Ana", "email": "ana@correo.com"},
            "items": [
                {
                    "producto_codigo": "PROD-001",
                    "cantidad": 2,
                    "precio_unitario": "10.00",
                },
                {
                    "producto_codigo": "PROD-002",
                    "cantidad": 1,
                    "precio_unitario": "25.50",
                },
            ],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["created_at"].endswith("Z")
    assert "movimientos_ids" in data and len(data["movimientos_ids"]) == 2
    assert data["total"] == "45.50" or str(data["total"]) == "45.50"
    assert (
        data["items"][0]["subtotal"] == "20.00"
        or str(data["items"][0]["subtotal"]) == "20.00"
    )
    assert (
        data["items"][1]["subtotal"] == "25.50"
        or str(data["items"][1]["subtotal"]) == "25.50"
    )
    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_ventas_post_422_varios(auth_headers):
    """T09: 422 para []/duplicado/2.00."""
    client, SessionLocal = _make_client()
    db = SessionLocal()
    p = Producto(
        sku="PROD-001",
        nombre="Producto A",
        categoria="consola",
        stock_inicial=10,
        estado="activo",
    )
    db.add(p)
    db.commit()
    db.close()

    # [] vacío
    assert (
        client.post(
            "/api/v1/ventas",
            json={"cliente": {"nombre": "Ana"}, "items": []},
            headers=auth_headers,
        ).status_code
        == 422
    )
    # duplicado tras normalización
    assert (
        client.post(
            "/api/v1/ventas",
            json={
                "cliente": {"nombre": "Ana"},
                "items": [
                    {
                        "producto_codigo": "PROD-001",
                        "cantidad": 1,
                        "precio_unitario": "10.00",
                    },
                    {
                        "producto_codigo": " prod-001 ",
                        "cantidad": 1,
                        "precio_unitario": "5.00",
                    },
                ],
            },
            headers=auth_headers,
        ).status_code
        == 422
    )
    # cantidad 2.00 float
    assert (
        client.post(
            "/api/v1/ventas",
            json={
                "cliente": {"nombre": "Ana"},
                "items": [
                    {
                        "producto_codigo": "PROD-001",
                        "cantidad": 2.00,
                        "precio_unitario": "10.00",
                    }
                ],
            },
            headers=auth_headers,
        ).status_code
        == 422
    )
    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_ventas_post_404_no_existe(auth_headers):
    """T09: 404 producto no encontrado."""
    client, _ = _make_client()
    resp = client.post(
        "/api/v1/ventas",
        json={
            "cliente": {"nombre": "Ana"},
            "items": [
                {
                    "producto_codigo": "NOEXISTE",
                    "cantidad": 1,
                    "precio_unitario": "10.00",
                }
            ],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 404
    assert "NOEXISTE" in resp.json()["detail"]
    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_ventas_post_400_stock_con_detalle(auth_headers):
    """T09: 400 stock insuficiente con detalle disponible/solicitado."""
    client, SessionLocal = _make_client()
    db = SessionLocal()
    p = Producto(
        sku="PROD-001",
        nombre="Producto A",
        categoria="consola",
        stock_inicial=2,
        estado="activo",
    )
    db.add(p)
    db.commit()
    db.close()

    resp = client.post(
        "/api/v1/ventas",
        json={
            "cliente": {"nombre": "Ana"},
            "items": [
                {
                    "producto_codigo": "PROD-001",
                    "cantidad": 5,
                    "precio_unitario": "10.00",
                }
            ],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "disponible" in resp.json()["detail"].lower()
    assert "solicitado" in resp.json()["detail"].lower()
    assert "PROD-001" in resp.json()["detail"]
    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_ventas_post_total_manipulado_ignorado(auth_headers):
    """T09: total manipulado ignorado, se persiste derivado."""
    client, SessionLocal = _make_client()
    db = SessionLocal()
    p = Producto(
        sku="PROD-001",
        nombre="Producto A",
        categoria="consola",
        stock_inicial=10,
        estado="activo",
    )
    db.add(p)
    db.commit()
    db.close()

    resp = client.post(
        "/api/v1/ventas",
        json={
            "cliente": {"nombre": "Ana"},
            "items": [
                {
                    "producto_codigo": "PROD-001",
                    "cantidad": 2,
                    "precio_unitario": "10.00",
                    "subtotal": "999.00",
                }
            ],
            "total": "999.00",
            "created_at": "2020-01-01T00:00:00Z",
            "id": 999,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert str(data["total"]) == "20.00"
    assert str(data["items"][0]["subtotal"]) == "20.00"
    assert data["id"] != 999
    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_ventas_get_orden_desc(auth_headers):
    """T09: GET /ventas 200 orden created_at DESC, id DESC."""
    client, SessionLocal = _make_client()
    db = SessionLocal()
    p = Producto(
        sku="PROD-001",
        nombre="Producto A",
        categoria="consola",
        stock_inicial=10,
        estado="activo",
    )
    db.add(p)
    db.commit()
    db.close()

    ids = []
    for i in range(3):
        resp = client.post(
            "/api/v1/ventas",
            json={
                "cliente": {"nombre": f"Cliente {i}"},
                "items": [
                    {
                        "producto_codigo": "PROD-001",
                        "cantidad": 1,
                        "precio_unitario": "10.00",
                    }
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        ids.append(resp.json()["id"])

    resp = client.get("/api/v1/ventas", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert [v["id"] for v in data] == sorted(ids, reverse=True)
    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_ventas_get_por_id_con_movimientos(auth_headers):
    """T09: GET /ventas/{id} 200 con movimientos_ids en GET /movimientos."""
    client, SessionLocal = _make_client()
    db = SessionLocal()
    p = Producto(
        sku="PROD-001",
        nombre="Producto A",
        categoria="consola",
        stock_inicial=10,
        estado="activo",
    )
    db.add(p)
    db.commit()
    db.close()

    resp = client.post(
        "/api/v1/ventas",
        json={
            "cliente": {"nombre": "Ana"},
            "items": [
                {
                    "producto_codigo": "PROD-001",
                    "cantidad": 1,
                    "precio_unitario": "10.00",
                }
            ],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    vid = resp.json()["id"]
    mid = resp.json()["movimientos_ids"][0]

    resp2 = client.get(f"/api/v1/ventas/{vid}", headers=auth_headers)
    assert resp2.status_code == 200
    assert resp2.json()["id"] == vid
    assert mid in resp2.json()["movimientos_ids"]

    # verificar en historial de movimientos
    resp_mov = client.get("/api/v1/movimientos", headers=auth_headers)
    assert resp_mov.status_code == 200
    mov_ids = {m["id"] for m in resp_mov.json()}
    assert mid in mov_ids
    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_ventas_401_sin_bearer():
    """T09: 401 sin Bearer para los 3 endpoints."""
    from app.main import app

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

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    assert (
        client.post(
            "/api/v1/ventas",
            json={
                "cliente": {"nombre": "Ana"},
                "items": [
                    {
                        "producto_codigo": "PROD-001",
                        "cantidad": 1,
                        "precio_unitario": "10.00",
                    }
                ],
            },
        ).status_code
        == 401
    )
    assert client.get("/api/v1/ventas").status_code == 401
    assert client.get("/api/v1/ventas/1").status_code == 401
    app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_ventas_get_404_id_no_existe(auth_headers):
    """T09: 404 id no existe para GET /{id}."""
    client, _ = _make_client()
    resp = client.get("/api/v1/ventas/9999", headers=auth_headers)
    assert resp.status_code == 404
    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]
