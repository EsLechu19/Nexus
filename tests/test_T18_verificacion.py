"""Tests de T18 — Verificación final constitución + AGENTS.md (RF-1..RF-5)."""

import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[1]),
    )


def test_T18_pytest_verde():
    """AGENTS: pytest --collect-only sin errores (100% verde se verifica en ejecución externa)."""
    result = _run([sys.executable, "-m", "pytest", "--collect-only", "-q"])
    assert result.returncode == 0, (
        f"pytest collect falló:\n{result.stdout}\n{result.stderr}"
    )
    assert (
        "test session starts" in result.stdout.lower()
        or "collected" in result.stdout.lower()
        or result.stdout.strip() == ""
    )


def test_T18_ruff_check():
    """AGENTS: ruff check . sin errores."""
    result = _run([sys.executable, "-m", "ruff", "check", "."])
    assert result.returncode == 0, (
        f"ruff check falló:\n{result.stdout}\n{result.stderr}"
    )
    assert "all checks passed" in result.stdout.lower() or result.stdout.strip() == ""


def test_T18_ruff_format():
    """AGENTS: ruff format --check sin errores."""
    result = _run([sys.executable, "-m", "ruff", "format", "--check", "."])
    assert result.returncode == 0, (
        f"ruff format falló:\n{result.stdout}\n{result.stderr}"
    )


def test_T18_mypy():
    """AGENTS: mypy app sin errores."""
    result = _run([sys.executable, "-m", "mypy", "app", "--ignore-missing-imports"])
    assert result.returncode == 0, f"mypy falló:\n{result.stdout}\n{result.stderr}"
    assert "success" in result.stdout.lower()


def test_T18_alembic_upgrade_head():
    """Constitución 5: alembic upgrade head ok."""
    result = _run([sys.executable, "-m", "alembic", "upgrade", "head"])
    assert result.returncode == 0, (
        f"alembic upgrade head falló:\n{result.stdout}\n{result.stderr}"
    )


def test_T18_docs_lista_5_endpoints():
    """T14/RF-1..RF-5: GET /docs y /openapi.json listan 5 endpoints."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    # /docs
    resp = client.get("/docs")
    assert resp.status_code == 200
    # /openapi.json
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    assert "/api/v1/productos" in paths
    assert "post" in paths["/api/v1/productos"]
    assert "get" in paths["/api/v1/productos"]
    assert "/api/v1/productos/{sku}" in paths
    sku_path = paths["/api/v1/productos/{sku}"]
    for method in ["get", "patch", "delete"]:
        assert method in sku_path, f"falta {method} en /{{sku}}"


def test_T18_constitucion_6_principios():
    """Constitución: 6 principios verificables y stack por capas."""
    content = Path("docs/constitution.md").read_text(encoding="utf-8")
    for n in ["1.", "2.", "3.", "4.", "5.", "6."]:
        assert n in content
    assert "routers" in content and "services" in content


def test_T18_no_expone_modelos_y_append_only():
    """AGENTS: schemas Pydantic y append-only (sin DELETE físico)."""
    router = Path("app/routers/productos.py").read_text(encoding="utf-8")
    assert "producto_service" in router
    assert "SELECT" not in router
    # Service no hace DELETE físico
    service = Path("app/services/producto_service.py").read_text(encoding="utf-8")
    assert "DELETE FROM" not in service
    assert 'estado = "inactivo"' in service or "inactivo" in service
