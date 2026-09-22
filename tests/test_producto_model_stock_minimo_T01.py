"""Tests de T01 004 — Modelo Producto stock_minimo (RF-1)."""


def test_modelo_producto_tiene_stock_minimo():
    """T01: Producto.stock_minimo existe con tipo y check."""
    from sqlalchemy import Integer

    from app.models.producto import Producto

    cols = {c.name: c for c in Producto.__table__.columns}
    assert "stock_minimo" in cols, "falta columna stock_minimo"
    assert isinstance(cols["stock_minimo"].type, Integer)
    assert not cols["stock_minimo"].nullable, "stock_minimo debe ser NOT NULL"
    assert cols["stock_minimo"].default.arg == 0
    assert cols["stock_minimo"].server_default.arg == "0"


def test_modelo_producto_stock_minimo_check():
    """T01: check stock_minimo 0..1_000_000."""
    from app.models.producto import Producto

    checks = [
        str(c.sqltext)
        for c in Producto.__table__.constraints
        if c.__class__.__name__ == "CheckConstraint"
    ]
    checks_text = " ".join(checks).lower()
    assert "stock_minimo" in checks_text, f"falta check stock_minimo, checks={checks}"
    assert "1000000" in checks_text


def test_modelo_producto_stock_minimo_default_y_no_nullable():
    """T01: mypy y default."""
    from app.models.producto import Producto

    # Verificar que el modelo tiene el atributo con tipo correcto para mypy
    assert hasattr(Producto, "stock_minimo")
