"""Tests de T17 — Integración endpoints POST/GET/PATCH/DELETE (RF-1..RF-5)."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.movimiento_inventario import MovimientoInventario  # noqa: F401
from app.models.producto import Producto  # noqa: F401


def _make_client():
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
    return client, TestingSessionLocal, engine


def test_T17_flujo_completo_RF1_a_RF5(auth_headers):
    """RF-1..RF-5: flujo POST, GET, PATCH, DELETE, 201/200/400/404/409, traza, inactivo, sin exponer modelos."""
    client, SessionLocal, _ = _make_client()

    # RF-2: listado vacío inicial
    resp = client.get("/api/v1/productos", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []

    # RF-1: POST válido con stock 0 (sin traza) y con stock >0 (con traza)
    resp = client.post(
        "/api/v1/productos",
        json={
            "sku": "INT-001",
            "nombre": "Juego A",
            "categoria": "videojuego",
            "stock_inicial": 0,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["sku"] == "INT-001"
    assert data["estado"] == "activo"
    assert "id" not in data and "created_at" not in data  # no expone modelo
    # Verificar traza no creada para stock 0
    db = SessionLocal()
    assert (
        db.query(MovimientoInventario)
        .filter(
            MovimientoInventario.producto_id
            == db.query(Producto).filter(Producto.sku == "INT-001").first().id
        )
        .count()
        == 0
    )
    db.close()

    resp = client.post(
        "/api/v1/productos",
        json={
            "sku": "INT-002",
            "nombre": "Consola B",
            "categoria": "consola",
            "stock_inicial": 10,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    db = SessionLocal()
    prod = db.query(Producto).filter(Producto.sku == "INT-002").first()
    assert (
        db.query(MovimientoInventario)
        .filter(MovimientoInventario.producto_id == prod.id)
        .count()
        == 1
    )
    mov = (
        db.query(MovimientoInventario)
        .filter(MovimientoInventario.producto_id == prod.id)
        .first()
    )
    assert mov.cantidad == 10 and mov.tipo == "entrada_inicial"
    db.close()

    # RF-1: POST duplicado -> 409, mensaje en español
    resp = client.post(
        "/api/v1/productos",
        json={"sku": "INT-001", "nombre": "Duplicado", "categoria": "videojuego"},
        headers=auth_headers,
    )
    assert resp.status_code == 409
    assert "ya existe" in resp.json()["detail"].lower()

    # RF-1: POST validación -> 422/400
    resp = client.post(
        "/api/v1/productos",
        json={"sku": "AB", "nombre": "Test", "categoria": "consola"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    resp = client.post(
        "/api/v1/productos",
        json={"sku": "INT-003", "nombre": "A", "categoria": "consola"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    resp = client.post(
        "/api/v1/productos",
        json={"sku": "INT-004", "nombre": "Test", "categoria": "juego"},
        headers=auth_headers,
    )
    assert resp.status_code == 422

    # RF-2: GET listado solo activos
    resp = client.get("/api/v1/productos", headers=auth_headers)
    assert resp.status_code == 200
    skus = {item["sku"] for item in resp.json()}
    assert skus == {"INT-001", "INT-002"}
    for item in resp.json():
        assert (
            "sku" in item
            and "nombre" in item
            and "categoria" in item
            and "stock_inicial" in item
        )
        assert "id" not in item

    # RF-3: GET detalle activo y normalizado
    resp = client.get("/api/v1/productos/INT-001", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["estado"] == "activo"
    resp = client.get("/api/v1/productos/  int-001 ", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["sku"] == "INT-001"
    # RF-3: GET no existe -> 404
    resp = client.get("/api/v1/productos/NO-EXISTE", headers=auth_headers)
    assert resp.status_code == 404
    assert "no encontrado" in resp.json()["detail"].lower()

    # RF-4: PATCH válido
    resp = client.patch(
        "/api/v1/productos/INT-001",
        json={"nombre": "Juego A Editado"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Juego A Editado"
    # PATCH sku distinto -> 400
    resp = client.patch(
        "/api/v1/productos/INT-001",
        json={"nombre": "Nuevo Valido", "sku": "OTRO-999"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    # PATCH payload vacío -> 422
    resp = client.patch("/api/v1/productos/INT-001", json={}, headers=auth_headers)
    assert resp.status_code == 422
    # PATCH no existe -> 404
    resp = client.patch(
        "/api/v1/productos/NO-EXISTE", json={"nombre": "Nuevo"}, headers=auth_headers
    )
    assert resp.status_code == 404

    # RF-5: DELETE válido
    resp = client.delete("/api/v1/productos/INT-001", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["estado"] == "inactivo"
    # Verificar excluido de listado pero visible en detalle
    resp = client.get("/api/v1/productos", headers=auth_headers)
    assert "INT-001" not in {item["sku"] for item in resp.json()}
    resp = client.get("/api/v1/productos/INT-001", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["estado"] == "inactivo"
    # DELETE ya inactivo -> 400
    resp = client.delete("/api/v1/productos/INT-001", headers=auth_headers)
    assert resp.status_code == 400
    # DELETE no existe -> 404
    resp = client.delete("/api/v1/productos/NO-EXISTE", headers=auth_headers)
    assert resp.status_code == 404

    # RF-4: PATCH inactivo -> 400
    resp = client.patch(
        "/api/v1/productos/INT-001", json={"nombre": "Intento"}, headers=auth_headers
    )
    assert resp.status_code == 400

    # Verificar que traza inicial permanece tras baja (RNF-1)
    db = SessionLocal()
    assert db.query(MovimientoInventario).count() == 1  # solo la de INT-002
    db.close()

    # Limpiar overrides
    app.dependency_overrides.clear()


def test_T17_mensajes_en_espanol_y_sin_exponer_modelos(auth_headers):
    """RNF-2 y AGENTS: mensajes en español y sin exponer SQLAlchemy."""
    client, _, _ = _make_client()
    # Crear y luego probar errores con mensajes
    client.post(
        "/api/v1/productos",
        json={"sku": "ESP-001", "nombre": "Test", "categoria": "videojuego"},
        headers=auth_headers,
    )
    resp = client.post(
        "/api/v1/productos",
        json={"sku": "ESP-001", "nombre": "Duplicado", "categoria": "videojuego"},
        headers=auth_headers,
    )
    assert "ya existe" in resp.json()["detail"].lower()
    resp = client.get("/api/v1/productos/NOPE", headers=auth_headers)
    assert "no encontrado" in resp.json()["detail"].lower()

    # Verificar que POST no expone id/created_at
    resp = client.post(
        "/api/v1/productos",
        json={"sku": "ESP-002", "nombre": "Otro", "categoria": "consola"},
        headers=auth_headers,
    )
    data = resp.json()
    for campo_prohibido in ["id", "created_at", "updated_at"]:
        assert campo_prohibido not in data
    app.dependency_overrides.clear()
