"""Tests de T15 — Integración endpoints Proveedores (TestClient + DB) RF-1..RF-5."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.proveedor import Proveedor  # noqa: F401


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
    return client, TestingSessionLocal


def test_T15_flujo_completo_RF1_a_RF5(auth_headers):
    """RF-1..RF-5: POST 201, GET 200, PATCH 200, DELETE 200, 400/404/409/422, null borra, inactivo, sin exponer modelos."""
    client, SessionLocal = _make_client()

    # RF-2: listado vacío
    assert client.get("/api/v1/proveedores", headers=auth_headers).json() == []

    # RF-1: POST sin contacto -> 201 nulls
    resp = client.post(
        "/api/v1/proveedores",
        json={"codigo": "T15-001", "nombre": "Proveedor A"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["codigo"] == "T15-001" and resp.json()["email"] is None
    assert "id" not in resp.json()

    # RF-1: POST con contacto -> 201 normalizado
    resp = client.post(
        "/api/v1/proveedores",
        json={
            "codigo": "  t15-002 ",
            "nombre": "Proveedor B",
            "email": "  TEST@A.COM ",
            "telefono": "+34 600 123 456",
            "direccion": "Calle 1",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["codigo"] == "T15-002"
    assert resp.json()["email"] == "test@a.com"

    # RF-1: duplicado -> 409
    resp = client.post(
        "/api/v1/proveedores",
        json={"codigo": "T15-001", "nombre": "Duplicado"},
        headers=auth_headers,
    )
    assert resp.status_code == 409
    assert "ya existe" in resp.json()["detail"].lower()

    # RF-1: validación -> 422
    assert (
        client.post(
            "/api/v1/proveedores",
            json={"codigo": "AB", "nombre": "Test"},
            headers=auth_headers,
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/proveedores",
            json={"codigo": "T15-003", "nombre": "A"},
            headers=auth_headers,
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/proveedores",
            json={"codigo": "T15-004", "nombre": "Test", "email": "sinarroba"},
            headers=auth_headers,
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/proveedores",
            json={"codigo": "T15-005", "nombre": "Test", "telefono": "123"},
            headers=auth_headers,
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/proveedores",
            json={"codigo": "T15-006", "nombre": "Test", "direccion": "ab"},
            headers=auth_headers,
        ).status_code
        == 422
    )

    # RF-2: GET listado solo activos ordenados, sin estado
    resp = client.get("/api/v1/proveedores", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert [d["codigo"] for d in data] == ["T15-001", "T15-002"]
    for item in data:
        assert "estado" not in item
        assert "id" not in item

    # RF-3: GET detalle activo y normalizado, inactivo trazabilidad, 404
    resp = client.get("/api/v1/proveedores/T15-001", headers=auth_headers)
    assert resp.status_code == 200 and resp.json()["estado"] == "activo"
    resp = client.get("/api/v1/proveedores/  t15-002 ", headers=auth_headers)
    assert resp.json()["codigo"] == "T15-002"
    assert (
        client.get("/api/v1/proveedores/NOPE", headers=auth_headers).status_code == 404
    )
    assert (
        "no encontrado"
        in client.get("/api/v1/proveedores/NOPE", headers=auth_headers)
        .json()["detail"]
        .lower()
    )

    # RF-4: PATCH válido, null borra, 400/404/422
    resp = client.patch(
        "/api/v1/proveedores/T15-002", json={"email": None}, headers=auth_headers
    )
    assert resp.status_code == 200 and resp.json()["email"] is None
    # Verificar que null borró pero ausente no cambia
    resp = client.patch(
        "/api/v1/proveedores/T15-002",
        json={"nombre": "Nuevo Nombre"},
        headers=auth_headers,
    )
    assert resp.json()["nombre"] == "Nuevo Nombre" and resp.json()["email"] is None
    # codigo distinto -> 400
    resp = client.patch(
        "/api/v1/proveedores/T15-002",
        json={"nombre": "Nombre Valido", "codigo": "OTRO-999"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    # mismo codigo se ignora
    resp = client.patch(
        "/api/v1/proveedores/T15-002",
        json={"nombre": "Otro", "codigo": "  t15-002 "},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    # payload vacío -> 422
    assert (
        client.patch(
            "/api/v1/proveedores/T15-002", json={}, headers=auth_headers
        ).status_code
        == 422
    )
    # inactivo no editable -> preparar baja
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "T15-007", "nombre": "Para Inactivar"},
        headers=auth_headers,
    )
    db = SessionLocal()
    prov = db.query(Proveedor).filter(Proveedor.codigo == "T15-007").first()
    prov.estado = "inactivo"
    db.commit()
    db.close()
    resp = client.patch(
        "/api/v1/proveedores/T15-007", json={"nombre": "Intento"}, headers=auth_headers
    )
    assert resp.status_code == 400
    assert resp.status_code == 400
    # no existe -> 404
    assert (
        client.patch(
            "/api/v1/proveedores/NOPE",
            json={"nombre": "Nombre Valido"},
            headers=auth_headers,
        ).status_code
        == 404
    )

    # RF-5: DELETE válido, ya inactivo 400, no existe 404, permite con stock/movimientos (no valida)
    resp = client.delete("/api/v1/proveedores/T15-002", headers=auth_headers)
    assert resp.status_code == 200 and resp.json()["estado"] == "inactivo"
    # excluido de listado pero visible en detalle
    assert "T15-002" not in {
        d["codigo"]
        for d in client.get("/api/v1/proveedores", headers=auth_headers).json()
    }
    resp = client.get("/api/v1/proveedores/T15-002", headers=auth_headers)
    assert resp.json()["estado"] == "inactivo"
    # ya inactivo -> 400
    assert (
        client.delete("/api/v1/proveedores/T15-002", headers=auth_headers).status_code
        == 400
    )
    assert (
        client.delete("/api/v1/proveedores/NOPE", headers=auth_headers).status_code
        == 404
    )

    # Verificar que 003 futuro rechazaría entrada con inactivo (simulado: proveedor inactivo no utilizable)
    # Si intentáramos crear movimiento con proveedor inactivo, el service de movimientos debería validar estado==activo
    db = SessionLocal()
    prov_inactivo = db.query(Proveedor).filter(Proveedor.codigo == "T15-002").first()
    assert prov_inactivo.estado == "inactivo"
    db.close()

    app.dependency_overrides.clear()


def test_T15_mensajes_espanol_y_sin_exponer_modelos(auth_headers):
    """RNF-2 y AGENTS: mensajes en español y sin exponer SQLAlchemy."""
    client, _ = _make_client()
    client.post(
        "/api/v1/proveedores",
        json={"codigo": "T15-100", "nombre": "Test"},
        headers=auth_headers,
    )
    resp = client.post(
        "/api/v1/proveedores",
        json={"codigo": "T15-100", "nombre": "Duplicado"},
        headers=auth_headers,
    )
    assert "ya existe" in resp.json()["detail"].lower()
    resp = client.get("/api/v1/proveedores/NOPE", headers=auth_headers)
    assert "no encontrado" in resp.json()["detail"].lower()
    resp = client.post(
        "/api/v1/proveedores",
        json={"codigo": "T15-101", "nombre": "Otro"},
        headers=auth_headers,
    )
    for campo in ["id", "created_at", "updated_at"]:
        assert campo not in resp.json()
    app.dependency_overrides.clear()
