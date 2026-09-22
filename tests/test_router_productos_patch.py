"""Tests de T12 — Router PATCH /api/v1/productos/{sku} edición (RF-4)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models.producto import Producto  # noqa: F401
from app.models.movimiento_inventario import MovimientoInventario  # noqa: F401


def _make_app_and_client():
    from app.routers.productos import router

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


def test_patch_edita_nombre_200(auth_headers):
    """RF-4: PATCH solo nombre -> 200."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/productos",
        json={"sku": "SKU-020", "nombre": "Original", "categoria": "videojuego"},
        headers=auth_headers,
    )
    resp = client.patch(
        "/api/v1/productos/SKU-020",
        json={"nombre": "Nuevo Nombre"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["nombre"] == "Nuevo Nombre"
    assert data["sku"] == "SKU-020"
    assert data["categoria"] == "videojuego"


def test_patch_edita_categoria_200(auth_headers):
    """RF-4: PATCH solo categoria -> 200."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/productos",
        json={"sku": "SKU-021", "nombre": "Test", "categoria": "videojuego"},
        headers=auth_headers,
    )
    resp = client.patch(
        "/api/v1/productos/SKU-021", json={"categoria": "consola"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["categoria"] == "consola"


def test_patch_ambos_campos_200(auth_headers):
    """RF-4: PATCH nombre y categoria -> 200."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/productos",
        json={"sku": "SKU-022", "nombre": "Original", "categoria": "videojuego"},
        headers=auth_headers,
    )
    resp = client.patch(
        "/api/v1/productos/SKU-022",
        json={"nombre": "Nuevo", "categoria": "accesorio"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Nuevo"
    assert resp.json()["categoria"] == "accesorio"


def test_patch_sku_mismo_se_ignora_200(auth_headers):
    """RF-4: sku mismo valor normalizado se ignora -> 200."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/productos",
        json={"sku": "SKU-023", "nombre": "Test", "categoria": "consola"},
        headers=auth_headers,
    )
    resp = client.patch(
        "/api/v1/productos/SKU-023",
        json={"nombre": "Cambiado", "sku": "  sku-023 "},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Cambiado"


def test_patch_sku_distinto_400(auth_headers):
    """RF-4: sku distinto -> 400 inmutable."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/productos",
        json={"sku": "SKU-024", "nombre": "Test", "categoria": "videojuego"},
        headers=auth_headers,
    )
    resp = client.patch(
        "/api/v1/productos/SKU-024",
        json={"nombre": "Nuevo", "sku": "OTRO-999"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "inmutable" in resp.json()["detail"].lower()


def test_patch_inactivo_400(auth_headers):
    """RF-4: inactivo no editable -> 400."""
    client, SessionLocal = _make_app_and_client()
    client.post(
        "/api/v1/productos",
        json={"sku": "SKU-025", "nombre": "Test", "categoria": "videojuego"},
        headers=auth_headers,
    )
    db = SessionLocal()
    prod = db.query(Producto).filter(Producto.sku == "SKU-025").first()
    prod.estado = "inactivo"
    db.commit()
    db.close()
    resp = client.patch(
        "/api/v1/productos/SKU-025", json={"nombre": "Nuevo"}, headers=auth_headers
    )
    assert resp.status_code == 400


def test_patch_no_encontrado_404(auth_headers):
    """RF-4: SKU inexistente -> 404."""
    client, _ = _make_app_and_client()
    resp = client.patch(
        "/api/v1/productos/NO-EXISTE", json={"nombre": "Nuevo"}, headers=auth_headers
    )
    assert resp.status_code == 404


def test_patch_payload_vacio_422(auth_headers):
    """RF-4: payload vacío sin nombre ni categoria -> 422."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/productos",
        json={"sku": "SKU-026", "nombre": "Test", "categoria": "videojuego"},
        headers=auth_headers,
    )
    resp = client.patch("/api/v1/productos/SKU-026", json={}, headers=auth_headers)
    assert resp.status_code == 422


def test_patch_validacion_422(auth_headers):
    """RF-4: validación Pydantic -> 422."""
    client, _ = _make_app_and_client()
    client.post(
        "/api/v1/productos",
        json={"sku": "SKU-027", "nombre": "Test", "categoria": "videojuego"},
        headers=auth_headers,
    )
    # nombre corto
    resp = client.patch(
        "/api/v1/productos/SKU-027", json={"nombre": "A"}, headers=auth_headers
    )
    assert resp.status_code == 422
    # categoria inválida
    resp = client.patch(
        "/api/v1/productos/SKU-027", json={"categoria": "juego"}, headers=auth_headers
    )
    assert resp.status_code == 422


def test_patch_delega_a_service(auth_headers):
    """Principio 3: router delega a service."""
    from pathlib import Path

    content = Path("app/routers/productos.py").read_text(encoding="utf-8")
    assert "actualizar_producto" in content
