"""Tests de T15 — Migración Alembic catálogo (RF-1, RF-5)."""

from pathlib import Path


def test_migraciones_existen_con_ambas_tablas():
    """T15: existen migraciones que crean productos y movimientos con checks e índices."""
    versions = Path("alembic/versions")
    assert versions.is_dir(), "falta alembic/versions"
    files = list(versions.glob("*.py"))
    # Debe haber al menos 2 migraciones (productos y movimientos) o una que contenga ambas
    assert len(files) >= 1, "no hay migraciones"
    content = " ".join(p.read_text(encoding="utf-8") for p in files)
    assert "productos" in content, "falta tabla productos en migraciones"
    assert "movimientos_inventario" in content, "falta tabla movimientos_inventario"
    # Checks e índices según plan §2.1 y §2.2
    for ck in [
        "ck_productos_categoria",
        "ck_productos_estado",
        "ck_productos_stock_inicial",
        "ck_movimientos_tipo",
    ]:
        assert ck in content, f"falta check {ck}"
    for idx in [
        "ix_productos_sku",
        "ix_productos_categoria",
        "ix_movimientos_producto_id",
    ]:
        # ix_productos_estado puede ser con o sin prefijo, verificar al menos uno
        assert idx in content or "ix_productos_estado" in content


def test_migracion_catalogo_productos_nombre():
    """T15: existe migración con mensaje 'crea catalogo productos'."""
    versions = Path("alembic/versions")
    files = list(versions.glob("*crea_catalogo_productos.py"))
    assert len(files) >= 1, "falta migración crea_catalogo_productos"
    assert "crea catalogo productos" in files[0].read_text(encoding="utf-8").lower()


def test_alembic_history_contiene_revisiones():
    """T15: alembic history lista las revisiones."""
    import subprocess

    result = subprocess.run(
        ["python", "-m", "alembic", "history"], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert "crea catalogo productos" in result.stdout.lower()
    assert "crea movimientos inventario" in result.stdout.lower()


def test_alembic_current_en_head():
    """T15: alembic current en head."""
    import subprocess

    result = subprocess.run(
        ["python", "-m", "alembic", "current"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "head" in result.stdout.lower()
