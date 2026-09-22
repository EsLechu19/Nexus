"""Tests de T07 — Router GET /api/v1/ventas y GET /{id} protegidos (RF-3, RF-4, RNF-5) — TDD."""

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
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T07-32chars-minimo!!")
    from app.services.auth_service import crear_token

    token = crear_token("admin@tienda.com")
    return {"Authorization": f"Bearer {token}"}


def test_get_ventas_sin_bearer_401(monkeypatch):
    """T07: GET /ventas y GET /{id} sin Bearer → 401 antes de SELECT."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-T07-32chars-minimo!!")
    client, _ = _make_client()
    assert client.get("/api/v1/ventas").status_code == 401
    assert client.get("/api/v1/ventas/1").status_code == 401
    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_get_ventas_vacio_devuelve_lista_vacia(monkeypatch):
    """T07: GET /ventas sin ventas → [] con Bearer válido."""
    client, _ = _make_client()
    headers = _auth_headers(monkeypatch)
    resp = client.get("/api/v1/ventas", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []
    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_get_ventas_orden_desc_y_get_por_id(monkeypatch):
    """T07: GET /ventas orden created_at DESC, id DESC; GET /{id} 200 con movimientos_ids en GET /movimientos."""
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

    # crear 3 ventas vía POST /ventas
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
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        ids.append(resp.json()["id"])

    # GET listado debe estar orden DESC (último primero)
    resp = client.get("/api/v1/ventas", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    # orden DESC por id (y created_at) → ids invertidos
    assert [v["id"] for v in data] == sorted(ids, reverse=True)
    for v in data:
        assert v["created_at"].endswith("Z")
        assert "movimientos_ids" in v and len(v["movimientos_ids"]) == 1
        assert v["total"] == "10.00" or str(v["total"]) == "10.00"
        assert (
            v["items"][0]["subtotal"] == "10.00"
            or str(v["items"][0]["subtotal"]) == "10.00"
        )

    # GET por id existente
    vid = ids[0]
    resp2 = client.get(f"/api/v1/ventas/{vid}", headers=headers)
    assert resp2.status_code == 200
    det = resp2.json()
    assert det["id"] == vid
    assert det["created_at"].endswith("Z")
    assert "movimientos_ids" in det

    # verificar que movimientos_ids existen en GET /movimientos
    resp_mov = client.get("/api/v1/movimientos", headers=headers)
    assert resp_mov.status_code == 200
    mov_ids = {m["id"] for m in resp_mov.json()}
    for mid in det["movimientos_ids"]:
        assert mid in mov_ids

    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_get_ventas_id_no_existe_404(monkeypatch):
    """T07: GET /ventas/{id} con id inexistente → 404."""
    client, _ = _make_client()
    headers = _auth_headers(monkeypatch)
    resp = client.get("/api/v1/ventas/999", headers=headers)
    assert resp.status_code == 404
    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


def test_ventas_no_expone_metodos_no_permitidos(monkeypatch):
    """T07: ventas no expone PUT/PATCH/DELETE → 405."""
    client, SessionLocal = _make_client()
    headers = _auth_headers(monkeypatch)
    db = SessionLocal()
    p = Producto(
        sku="PROD-002",
        nombre="Producto B",
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
                    "producto_codigo": "PROD-002",
                    "cantidad": 1,
                    "precio_unitario": "5.00",
                }
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    vid = resp.json()["id"]
    assert client.put(f"/api/v1/ventas/{vid}", headers=headers).status_code == 405
    assert client.patch(f"/api/v1/ventas/{vid}", headers=headers).status_code == 405
    assert client.delete(f"/api/v1/ventas/{vid}", headers=headers).status_code == 405
    assert client.put("/api/v1/ventas", headers=headers).status_code == 405
    client.app.dependency_overrides.clear()  # type: ignore[attr-defined]
