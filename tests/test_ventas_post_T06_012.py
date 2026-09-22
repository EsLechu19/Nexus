"""Tests de T06 — Router POST /api/v1/ventas protegido (RF-1, RF-2, RNF-5) — TDD."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models.producto import Producto  # noqa: F401
from app.models.venta import Venta  # noqa: F401
from app.models.venta_item import VentaItem  # noqa: F401


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


def _auth_headers(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T06-32chars-minimo!!")
    from app.services.auth_service import crear_token

    token = crear_token("admin@tienda.com")
    return {"Authorization": f"Bearer {token}"}


def test_post_sin_bearer_401_antes_de_bd(monkeypatch):
    """T06: sin Bearer → 401 antes de SELECT (no crea venta)."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T06-32chars-minimo!!")
    client, _ = _make_client()
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
    )
    assert resp.status_code == 401
    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_post_valido_201_con_total_y_movimientos(monkeypatch):
    """T06: con Bearer válido y carrito válido → 201 con id, created_at Z, cliente normalizado, items subtotal, total y movimientos_ids."""
    client, SessionLocal = _make_client()
    headers = _auth_headers(monkeypatch)
    # crear producto
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
            "cliente": {"nombre": "  Ana  ", "email": "ANA@correo.com"},
            "items": [
                {
                    "producto_codigo": "  prod-001 ",
                    "cantidad": 2,
                    "precio_unitario": "10.00",
                }
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "id" in data and isinstance(data["id"], int)
    assert data["created_at"].endswith("Z")
    assert data["cliente"]["nombre"] == "Ana"
    assert data["cliente"]["email"] == "ana@correo.com"
    assert len(data["items"]) == 1
    assert (
        data["items"][0]["subtotal"] == "20.00" or data["items"][0]["subtotal"] == 20.00
    )
    assert data["total"] == "20.00" or data["total"] == 20.00
    assert "movimientos_ids" in data and len(data["movimientos_ids"]) == 1
    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_post_422_varios_casos(monkeypatch):
    """T06: 422 para []/>20/duplicado/2.00/10.123."""
    client, SessionLocal = _make_client()
    headers = _auth_headers(monkeypatch)
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
            headers=headers,
        ).status_code
        == 422
    )
    # >20
    items_21 = [
        {"producto_codigo": f"PROD-{i:03d}", "cantidad": 1, "precio_unitario": "1.00"}
        for i in range(21)
    ]
    assert (
        client.post(
            "/api/v1/ventas",
            json={"cliente": {"nombre": "Ana"}, "items": items_21},
            headers=headers,
        ).status_code
        == 422
    )
    # duplicado
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
            headers=headers,
        ).status_code
        == 422
    )
    # cantidad 2.00 decimal
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
            headers=headers,
        ).status_code
        == 422
    )
    # precio >2 decimales
    assert (
        client.post(
            "/api/v1/ventas",
            json={
                "cliente": {"nombre": "Ana"},
                "items": [
                    {
                        "producto_codigo": "PROD-001",
                        "cantidad": 1,
                        "precio_unitario": "10.123",
                    }
                ],
            },
            headers=headers,
        ).status_code
        == 422
    )
    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_post_404_no_encontrado_y_400_inactivo_stock(monkeypatch):
    """T06: 404 no encontrado, 400 inactivo/stock con detalle."""
    client, SessionLocal = _make_client()
    headers = _auth_headers(monkeypatch)
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

    # no encontrado
    resp = client.post(
        "/api/v1/ventas",
        json={
            "cliente": {"nombre": "Ana"},
            "items": [
                {"producto_codigo": "NOPE", "cantidad": 1, "precio_unitario": "10.00"}
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 404
    assert "NOPE" in resp.json()["detail"]

    # inactivo
    db = SessionLocal()
    p2 = Producto(
        sku="PROD-002",
        nombre="Producto B",
        categoria="consola",
        stock_inicial=10,
        estado="inactivo",
    )
    db.add(p2)
    db.commit()
    db.close()
    resp = client.post(
        "/api/v1/ventas",
        json={
            "cliente": {"nombre": "Ana"},
            "items": [
                {
                    "producto_codigo": "PROD-002",
                    "cantidad": 1,
                    "precio_unitario": "10.00",
                }
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 400
    assert "PROD-002" in resp.json()["detail"]

    # stock insuficiente
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
        headers=headers,
    )
    assert resp.status_code == 400
    assert "PROD-001" in resp.json()["detail"]
    assert "disponible" in resp.json()["detail"].lower()
    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_post_total_enviado_ignorado(monkeypatch):
    """T06: total/subtotal/created_at/id enviados se ignoran."""
    client, SessionLocal = _make_client()
    headers = _auth_headers(monkeypatch)
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
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    # debe ser derivado, no 999
    assert str(data["total"]) == "20.00"
    assert str(data["items"][0]["subtotal"]) == "20.00"
    assert data["id"] != 999
    assert data["created_at"] != "2020-01-01T00:00:00Z"
    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]
