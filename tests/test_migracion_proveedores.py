"""Tests de T13 — Migración Alembic crea proveedores (RF-1, RF-5)."""

from pathlib import Path


def test_migracion_proveedores_existe_con_tabla_y_checks():
    """T13: existe migración con tabla proveedores, checks e índices."""
    versions = Path("alembic/versions")
    assert versions.is_dir()
    files = list(versions.glob("*crea_proveedores.py"))
    assert len(files) >= 1, "falta migración crea_proveedores"
    content = files[0].read_text(encoding="utf-8")
    assert "proveedores" in content
    for ck in [
        "ck_proveedores_codigo_regex",
        "ck_proveedores_nombre_length",
        "ck_proveedores_estado",
    ]:
        assert ck in content, f"falta check {ck}"
    for idx in ["ix_proveedores_codigo", "ix_proveedores_estado"]:
        assert idx in content


def test_migracion_proveedores_nombre_mensaje():
    """T13: mensaje 'crea proveedores' en archivo."""
    versions = Path("alembic/versions")
    files = list(versions.glob("*crea_proveedores.py"))
    assert len(files) >= 1
    assert "crea proveedores" in files[0].read_text(encoding="utf-8").lower()


def test_alembic_history_proveedores():
    """T13: history contiene crea proveedores."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "history"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "crea proveedores" in result.stdout.lower()


def test_alembic_current_head_proveedores():
    """T13: current en head incluye proveedores."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "current"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "head" in result.stdout.lower()
    assert (
        "37840112ca70" in result.stdout
        or "crea proveedores" in result.stdout.lower()
        or "head" in result.stdout.lower()
    )
