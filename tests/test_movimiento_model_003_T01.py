"""Tests de T01 003 — Modelo MovimientoInventario extendido (RF-1, RF-2, RF-3)."""


def test_T01_modelo_extendido_existe():
    from app.models.movimiento_inventario import MovimientoInventario

    assert MovimientoInventario.__tablename__ == "movimientos_inventario"
    cols = {c.name for c in MovimientoInventario.__table__.columns}
    for col in [
        "id",
        "producto_id",
        "proveedor_id",
        "tipo",
        "cantidad",
        "motivo",
        "created_at",
    ]:
        assert col in cols, f"falta columna {col}"


def test_T01_columnas_tipos_y_nulabilidad():
    from sqlalchemy import DateTime, Integer, String

    from app.models.movimiento_inventario import MovimientoInventario
    from app.models.producto import Producto  # noqa: F401

    # Importar para registrar tablas en metadata
    from app.models.proveedor import Proveedor  # noqa: F401

    cols = {c.name: c for c in MovimientoInventario.__table__.columns}
    assert (
        isinstance(cols["producto_id"].type, Integer)
        and not cols["producto_id"].nullable
    )
    assert (
        isinstance(cols["proveedor_id"].type, Integer) and cols["proveedor_id"].nullable
    )  # NULL para salida
    assert isinstance(cols["tipo"].type, String)
    assert isinstance(cols["cantidad"].type, Integer)
    assert isinstance(cols["motivo"].type, String) and cols["motivo"].nullable
    assert isinstance(cols["created_at"].type, DateTime)
    # proveedor_id FK
    assert any(
        "proveedores" in fk.target_fullname
        for fk in MovimientoInventario.__table__.foreign_keys
    )
    assert any(
        "productos" in fk.target_fullname
        for fk in MovimientoInventario.__table__.foreign_keys
    )
    # tipo check
    checks = " ".join(
        str(c.sqltext).lower()
        for c in MovimientoInventario.__table__.constraints
        if c.__class__.__name__ == "CheckConstraint"
    )
    assert "entrada" in checks and "salida" in checks
    assert "cantidad" in checks and "1000000" in checks
    assert "motivo" in checks


def test_T01_indices():
    from app.models.movimiento_inventario import MovimientoInventario

    idx_cols = {
        c.name for idx in MovimientoInventario.__table__.indexes for c in idx.columns
    }
    for col in ["producto_id", "proveedor_id", "tipo"]:
        assert col in idx_cols, f"falta índice {col}"
    # created_at índice
    assert "created_at" in idx_cols or any(
        "created_at" in str(idx) for idx in MovimientoInventario.__table__.indexes
    )


def test_T01_append_only_sin_updated_at():
    from app.models.movimiento_inventario import MovimientoInventario

    cols = {c.name for c in MovimientoInventario.__table__.columns}
    assert "updated_at" not in cols
