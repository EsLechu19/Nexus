"""Tests de T01 — estructura base del catálogo (RF: ninguno, infra)."""

from pathlib import Path
import subprocess


def _nexus_root() -> Path:
    # Nexus/tests/test_estructura.py -> Nexus
    return Path(__file__).resolve().parents[1]


def test_estructura_carpetas_por_capas_existe():
    """Principio 1 y 3: existen routers/, services/, models/, schemas/."""
    root = _nexus_root()
    for rel in ["app/models", "app/schemas", "app/services", "app/routers"]:
        assert (root / rel).is_dir(), f"falta directorio {rel}"


def test_paquetes_python_con_init():
    """Cada capa es un paquete Python importable."""
    root = _nexus_root()
    for rel in [
        "app/__init__.py",
        "app/models/__init__.py",
        "app/schemas/__init__.py",
        "app/services/__init__.py",
        "app/routers/__init__.py",
    ]:
        assert (root / rel).is_file(), f"falta {rel}"


def test_rama_001_productos_catalogo_existe():
    """T01 exige rama 001-productos-catalogo creada."""
    result = subprocess.run(
        ["git", "branch", "--list", "001-productos-catalogo"],
        capture_output=True,
        text=True,
        cwd=str(_nexus_root().parent),
    )
    assert "001-productos-catalogo" in result.stdout
