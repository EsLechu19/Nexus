"""Tests de T16 — Verificación final proveedores (RF-1..RF-5, constitución + AGENTS)."""

import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]):
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[1]),
    )


def test_T16_pytest_verde():
    """AGENTS: pytest --collect-only sin errores."""
    result = _run([sys.executable, "-m", "pytest", "--collect-only", "-q"])
    assert result.returncode == 0, result.stderr
    assert (
        "passed" in result.stdout.lower()
        or "collected" in result.stdout.lower()
        or result.stdout.strip() == ""
    )


def test_T16_ruff_check():
    result = _run([sys.executable, "-m", "ruff", "check", "."])
    assert result.returncode == 0, (
        f"ruff check falló:\n{result.stdout}\n{result.stderr}"
    )


def test_T16_ruff_format():
    result = _run([sys.executable, "-m", "ruff", "format", "--check", "."])
    assert result.returncode == 0, (
        f"ruff format falló:\n{result.stdout}\n{result.stderr}"
    )


def test_T16_mypy():
    result = _run([sys.executable, "-m", "mypy", "app", "--ignore-missing-imports"])
    assert result.returncode == 0, f"mypy falló:\n{result.stdout}\n{result.stderr}"
    assert "success" in result.stdout.lower()


def test_T16_alembic_upgrade_head():
    result = _run([sys.executable, "-m", "alembic", "upgrade", "head"])
    assert result.returncode == 0, (
        f"alembic upgrade head falló:\n{result.stdout}\n{result.stderr}"
    )


def test_T16_docs_10_endpoints():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    assert client.get("/docs").status_code == 200
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    # 5 productos + 5 proveedores = 10
    assert "/api/v1/productos" in paths and "/api/v1/proveedores" in paths
    assert (
        "/api/v1/productos/{sku}" in paths and "/api/v1/proveedores/{codigo}" in paths
    )
    total = sum(len(m) for m in paths.values())
    assert total >= 10
    # Verificar proveedores endpoints
    assert "post" in paths["/api/v1/proveedores"]
    assert "get" in paths["/api/v1/proveedores"]
    prov_det = paths["/api/v1/proveedores/{codigo}"]
    assert "get" in prov_det and "patch" in prov_det and "delete" in prov_det


def test_T16_proveedor_id_expuesto_para_003():
    """Plan §2.3 y §6: proveedor_id Integer para 003."""
    from sqlalchemy import Integer

    from app.models.proveedor import Proveedor

    assert isinstance(Proveedor.__table__.c.id.type, Integer)
    # Verificar que el modelo tiene id PK Integer
    assert Proveedor.__table__.c.id.primary_key is True
    # Verificar que el plan menciona proveedor_id Integer
    assert (
        Path("specs/002-proveedores/plan.md")
        .read_text(encoding="utf-8")
        .count("proveedor_id")
        >= 1
    )


def test_T16_constitucion_6_principios_y_capas():
    content = Path("docs/constitution.md").read_text(encoding="utf-8")
    for n in ["1.", "2.", "3.", "4.", "5.", "6."]:
        assert n in content
    assert "routers" in content and "services" in content
    # Verificar estructura por capas existe
    for p in ["app/routers", "app/services", "app/models", "app/schemas"]:
        assert Path(p).is_dir()
