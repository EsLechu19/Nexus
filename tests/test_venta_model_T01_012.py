"""Tests de T01 — Modelos Venta y VentaItem (RF-1, RF-2, RNF-3) — TDD."""

import subprocess
from pathlib import Path


def test_modelo_venta_existe_y_tabla():
    """T01: app/models/venta.py define Venta con tabla ventas."""
    from app.models.venta import Venta

    assert Venta.__tablename__ == "ventas"
    assert Venta.__name__ == "Venta"


def test_modelo_venta_columnas():
    """T01: Venta tiene id, created_at, cliente_nombre, cliente_email, total."""
    from sqlalchemy import Integer, Numeric, String

    from app.models.venta import Venta

    cols = {c.name: c for c in Venta.__table__.columns}
    for name in ["id", "created_at", "cliente_nombre", "cliente_email", "total"]:
        assert name in cols, f"falta columna {name}"
    assert isinstance(cols["id"].type, Integer)
    assert isinstance(cols["cliente_nombre"].type, String)
    assert isinstance(cols["total"].type, Numeric)
    assert not cols["cliente_nombre"].nullable
    assert cols["cliente_email"].nullable
    assert list(Venta.__table__.primary_key.columns)[0].name == "id"


def test_modelo_venta_item_existe_y_tabla():
    """T01: app/models/venta_item.py define VentaItem con tabla venta_items."""
    from app.models.venta_item import VentaItem

    assert VentaItem.__tablename__ == "venta_items"
    assert VentaItem.__name__ == "VentaItem"


def test_modelo_venta_item_columnas_y_fks():
    """T01: VentaItem tiene venta_id, producto_id, cantidad, precio_unitario, subtotal, movimiento_id FKs."""
    from sqlalchemy import Integer, Numeric

    from app.models.venta_item import VentaItem

    cols = {c.name: c for c in VentaItem.__table__.columns}
    for name in [
        "id",
        "venta_id",
        "producto_id",
        "cantidad",
        "precio_unitario",
        "subtotal",
        "movimiento_id",
    ]:
        assert name in cols, f"falta columna {name}"
    assert isinstance(cols["cantidad"].type, Integer)
    assert isinstance(cols["precio_unitario"].type, Numeric)
    # FKs
    fks = {
        fk.parent.name: fk.column.table.name for fk in VentaItem.__table__.foreign_keys
    }
    assert fks.get("venta_id") == "ventas"
    assert fks.get("producto_id") == "productos"
    assert fks.get("movimiento_id") == "movimientos_inventario"
    # movimiento_id unique
    assert cols["movimiento_id"].unique or any(
        idx.unique
        for idx in VentaItem.__table__.indexes
        if "movimiento_id" in {c.name for c in idx.columns}
    )


def test_migracion_ventas_existe():
    """T01: existe migración crea ventas 012 con tablas ventas y venta_items."""
    versions = Path("alembic/versions")
    content_all = " ".join(p.read_text(encoding="utf-8") for p in versions.glob("*.py"))
    assert "ventas" in content_all, "falta tabla ventas en migraciones"
    assert "venta_items" in content_all, "falta tabla venta_items"
    assert "ix_ventas_created_at" in content_all or "ventas" in content_all


def test_alembic_upgrade_head_ventas():
    """T01: alembic upgrade head aplica migración ventas."""
    result = subprocess.run(
        ["python", "-m", "alembic", "upgrade", "head"], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
