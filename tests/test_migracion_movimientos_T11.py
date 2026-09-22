"""Tests de T11 — Migración Alembic extiende movimientos 003 (RF-1, RF-2)."""

from pathlib import Path


def test_migracion_extiende_existe_con_columnas_e_indices():
    """T11: existe migración con proveedor_id, motivo, tipo ampliado e índices."""
    versions = Path("alembic/versions")
    files = list(versions.glob("*extiende_movimientos*003*.py"))
    assert len(files) >= 1, "falta migración extiende movimientos 003"
    content = files[0].read_text(encoding="utf-8")
    assert "proveedor_id" in content
    assert "motivo" in content
    for ck in [
        "ck_movimientos_tipo",
        "ck_movimientos_motivo",
        "ck_movimientos_proveedor_entrada",
    ]:
        assert ck in content
    for idx in [
        "ix_movimientos_proveedor_id",
        "ix_movimientos_tipo",
        "ix_movimientos_created_at",
    ]:
        assert idx in content
    assert "proveedores" in content


def test_migracion_mensaje_extiende():
    versions = Path("alembic/versions")
    files = list(versions.glob("*extiende_movimientos*003*.py"))
    assert len(files) >= 1
    assert "extiende movimientos" in files[0].read_text(encoding="utf-8").lower()


def test_alembic_history_extiende():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "history"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "extiende movimientos" in result.stdout.lower()


def test_alembic_current_head_extiende():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "current"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "9111dba96a53" in result.stdout or "head" in result.stdout.lower()
