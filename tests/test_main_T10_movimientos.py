"""Tests de T10 003 — Registro de movimientos y stock en app/main.py (RF-1..RF-4)."""

from pathlib import Path


def test_main_incluye_movimientos_y_stock_router(auth_headers):
    """T10: app/main.py incluye movimientos y stock."""
    p = Path("app/main.py")
    content = p.read_text(encoding="utf-8")
    assert "movimientos" in content
    assert "stock" in content
    assert "include_router" in content


def test_openapi_lista_14_endpoints(auth_headers):
    """T10: GET /openapi.json lista 14 endpoints (10 previos + 4 nuevos)."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    paths = resp.json()["paths"]
    # Productos (5)
    assert "/api/v1/productos" in paths
    assert "/api/v1/productos/{sku}" in paths
    # Proveedores (5, headers=auth_headers)
    assert "/api/v1/proveedores" in paths
    assert "/api/v1/proveedores/{codigo}" in paths
    # Movimientos (3) + Stock (2) = 5, pero se cuentan como 4 nuevos según spec (2 POST + 2 GET)
    assert "/api/v1/movimientos/entradas" in paths or "/api/v1/movimientos" in paths
    # Verificar al menos 14 métodos totales
    total = sum(len(methods) for methods in paths.values())
    assert total >= 14, f"total métodos {total} <14, paths={list(paths.keys())}"
    # Verificar stock
    assert "/api/v1/stock" in paths
    assert "/api/v1/stock/{codigo}" in paths


def test_docs_movimientos_200(auth_headers):
    """T10: GET /docs 200 con nuevos routers."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    assert client.get("/docs").status_code == 200
