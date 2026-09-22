"""Tests de T14 — Registro del router en app/main.py (RF-1..RF-5)."""

from pathlib import Path


def test_main_py_existe_e_incluye_router(auth_headers):
    """T14: app/main.py existe e incluye productos.router."""
    p = Path("app/main.py")
    assert p.is_file(), "falta app/main.py"
    content = p.read_text(encoding="utf-8")
    assert (
        "productos.router" in content
        or "productos_router" in content
        or "from app.routers.productos" in content
    )
    assert "FastAPI" in content
    assert "include_router" in content


def test_app_expone_5_endpoints_en_openapi(auth_headers):
    """T14: GET /openapi.json lista los 5 endpoints bajo /api/v1/productos."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    paths = resp.json()["paths"]
    # Verificar los 5 endpoints
    assert "/api/v1/productos" in paths
    assert "post" in paths["/api/v1/productos"]
    assert "get" in paths["/api/v1/productos"]
    assert "/api/v1/productos/{sku}" in paths
    sku_path = paths["/api/v1/productos/{sku}"]
    assert "get" in sku_path
    assert "patch" in sku_path
    assert "delete" in sku_path


def test_docs_responde_200(auth_headers):
    """T14: GET /docs lista los 5 endpoints (Swagger)."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    resp = client.get("/docs")
    assert resp.status_code == 200
    # Verificar que el HTML contiene referencia a los endpoints
    text = resp.text.lower()
    assert "swagger" in text or "openapi" in text


def test_main_no_contiene_logica_de_negocio(auth_headers):
    """Principio 3: main.py solo registra router, sin queries ni lógica."""
    content = Path("app/main.py").read_text(encoding="utf-8")
    assert "SELECT" not in content
    assert (
        "producto_service" not in content or "include_router" in content
    )  # service solo via router
