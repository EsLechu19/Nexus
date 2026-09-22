"""Tests de T12 — Registro de proveedores en app/main.py (RF-1..RF-5)."""

from pathlib import Path


def test_main_incluye_proveedores_router(auth_headers):
    """T12: app/main.py incluye proveedores.router junto a productos."""
    p = Path("app/main.py")
    assert p.is_file()
    content = p.read_text(encoding="utf-8")
    assert "proveedores" in content
    assert "productos.router" in content or "productos_router" in content
    assert "proveedores.router" in content or "proveedores_router" in content


def test_openapi_lista_10_endpoints(auth_headers):
    """T12: GET /openapi.json lista 10 endpoints (5 productos + 5 proveedores)."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    paths = resp.json()["paths"]
    # Productos
    assert "/api/v1/productos" in paths
    assert "post" in paths["/api/v1/productos"]
    assert "get" in paths["/api/v1/productos"]
    assert "/api/v1/productos/{sku}" in paths
    sku_path = paths["/api/v1/productos/{sku}"]
    assert "get" in sku_path and "patch" in sku_path and "delete" in sku_path
    # Proveedores
    assert "/api/v1/proveedores" in paths
    assert "post" in paths["/api/v1/proveedores"]
    assert "get" in paths["/api/v1/proveedores"]
    assert "/api/v1/proveedores/{codigo}" in paths
    cod_path = paths["/api/v1/proveedores/{codigo}"]
    assert "get" in cod_path and "patch" in cod_path and "delete" in cod_path
    # Total métodos = 10
    total = sum(len(methods) for methods in paths.values())
    # Al menos 10 (puede haber más por docs, pero productos+proveedores =10)
    assert total >= 10


def test_docs_proveedores_200(auth_headers):
    """T12: GET /docs 200 con ambos routers."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "swagger" in resp.text.lower() or "openapi" in resp.text.lower()
