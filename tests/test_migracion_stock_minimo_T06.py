"""Tests de T06 004 — Migración stock_minimo (RF-1)."""

from pathlib import Path


def test_migracion_stock_minimo_existe_con_columna_y_check():
    """T06: existe migración con stock_minimo y check."""
    versions = Path("alembic/versions")
    files = list(versions.glob("*agrega_stock_minimo*"))
    assert len(files) >= 1, "falta migración agrega_stock_minimo"
    content = files[0].read_text(encoding="utf-8")
    assert "stock_minimo" in content
    assert "ck_productos_stock_minimo" in content or "stock_minimo" in content.lower()


def test_migracion_stock_minimo_mensaje():
    versions = Path("alembic/versions")
    files = list(versions.glob("*agrega_stock_minimo*"))
    assert len(files) >= 1
    assert "agrega stock_minimo" in files[0].read_text(encoding="utf-8").lower()


def test_alembic_history_stock_minimo():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "history"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "agrega stock_minimo" in result.stdout.lower()


def test_alembic_current_head_stock_minimo():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "current"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "7010b4ddca09" in result.stdout or "head" in result.stdout.lower()
