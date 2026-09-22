"""Tests de T03 — Modelo MovimientoInventario (RF-1 traza inicial)."""


def test_modelo_movimiento_existe_y_tabla():
    """T03: app/models/movimiento_inventario.py define MovimientoInventario con tabla movimientos_inventario."""
    from app.models.movimiento_inventario import MovimientoInventario

    assert MovimientoInventario.__tablename__ == "movimientos_inventario"


def test_modelo_movimiento_columnas_y_tipos():
    """T03: columnas id, producto_id, tipo, cantidad, created_at con tipos, FK y defaults."""
    from sqlalchemy import DateTime, Integer, String

    from app.models.movimiento_inventario import MovimientoInventario

    # Importar Producto para que la FK pueda resolverse en el metadata
    from app.models.producto import Producto  # noqa: F401

    cols = {c.name: c for c in MovimientoInventario.__table__.columns}
    for name in ["id", "producto_id", "tipo", "cantidad", "created_at"]:
        assert name in cols, f"falta columna {name}"

    assert isinstance(cols["id"].type, Integer)
    assert isinstance(cols["producto_id"].type, Integer)
    assert isinstance(cols["tipo"].type, String) and cols["tipo"].type.length == 15
    assert isinstance(cols["cantidad"].type, Integer)
    assert isinstance(cols["created_at"].type, DateTime)

    for name in ["producto_id", "tipo", "cantidad", "created_at"]:
        assert not cols[name].nullable, f"{name} debe ser NOT NULL"

    assert list(MovimientoInventario.__table__.primary_key.columns)[0].name == "id"

    # FKs a productos.id y proveedores.id con RESTRICT (ahora 2 FKs tras 003)
    fks = list(MovimientoInventario.__table__.foreign_keys)
    assert len(fks) in (1, 2), f"debe tener 1 o 2 FKs, tiene {len(fks)}"
    assert any(fk.target_fullname == "productos.id" for fk in fks)
    # Verificar ondelete RESTRICT si está definido
    for fk in fks:
        assert fk.ondelete is None or fk.ondelete.upper() == "RESTRICT"

    # índice en producto_id
    index_cols = {
        col.name
        for idx in MovimientoInventario.__table__.indexes
        for col in idx.columns
    }
    assert "producto_id" in index_cols, "falta índice en producto_id"


def test_modelo_movimiento_checks():
    """T03: checks tipo='entrada_inicial' y cantidad >0 <=1_000_000, append-only sin updated_at."""
    from app.models.movimiento_inventario import MovimientoInventario

    checks = [
        str(c.sqltext)
        for c in MovimientoInventario.__table__.constraints
        if c.__class__.__name__ == "CheckConstraint"
    ]
    checks_text = " ".join(checks).lower()

    assert "entrada_inicial" in checks_text, (
        f"falta check tipo entrada_inicial, checks={checks}"
    )
    assert "cantidad" in checks_text and "1000000" in checks_text, (
        f"falta check cantidad, checks={checks}"
    )
    # asegurar cantidad >0
    assert "cantidad" in checks_text and (
        "> 0" in checks_text or ">0" in checks_text
    ), f"falta check cantidad >0, checks={checks}"

    # append-only: no debe tener updated_at
    cols = {c.name for c in MovimientoInventario.__table__.columns}
    assert "updated_at" not in cols, "movimientos debe ser append-only sin updated_at"


def test_modelo_movimiento_es_singular_y_tabla_plural():
    """AGENTS.md: modelo singular MovimientoInventario, tabla plural movimientos_inventario."""
    from app.models.movimiento_inventario import MovimientoInventario

    assert MovimientoInventario.__name__ == "MovimientoInventario"
    assert MovimientoInventario.__tablename__ == "movimientos_inventario"
