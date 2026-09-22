"""Tests de T02 — Modelo Producto (RF-1, RF-4, RF-5)."""


def test_modelo_producto_existe_y_tabla():
    """T02: app/models/producto.py define Producto con tabla productos."""
    from app.models.producto import Producto

    assert Producto.__tablename__ == "productos"


def test_modelo_producto_columnas_y_tipos():
    """T02: columnas id, sku, nombre, categoria, stock_inicial, estado, created_at, updated_at con tipos y defaults."""
    from sqlalchemy import Integer, String
    from app.models.producto import Producto

    cols = {c.name: c for c in Producto.__table__.columns}
    # existencia
    for name in [
        "id",
        "sku",
        "nombre",
        "categoria",
        "stock_inicial",
        "estado",
        "created_at",
        "updated_at",
    ]:
        assert name in cols, f"falta columna {name}"

    # tipos
    assert isinstance(cols["id"].type, Integer)
    assert isinstance(cols["sku"].type, String) and cols["sku"].type.length == 20
    assert isinstance(cols["nombre"].type, String) and cols["nombre"].type.length == 100
    assert isinstance(cols["categoria"].type, String)
    assert isinstance(cols["stock_inicial"].type, Integer)
    assert isinstance(cols["estado"].type, String)

    # NOT NULL
    for name in [
        "sku",
        "nombre",
        "categoria",
        "stock_inicial",
        "estado",
        "created_at",
        "updated_at",
    ]:
        assert not cols[name].nullable, f"{name} debe ser NOT NULL"

    # defaults
    assert cols["stock_inicial"].default.arg == 0
    assert cols["estado"].default.arg == "activo"

    # PK
    assert list(Producto.__table__.primary_key.columns)[0].name == "id"


def test_modelo_producto_indices_y_unique():
    """T02: sku UNIQUE, índices en sku, categoria y estado."""
    from app.models.producto import Producto

    # sku unique constraint / index
    sku_col = Producto.__table__.c.sku
    assert sku_col.unique is True or any(
        idx.unique and sku_col in idx.columns.values()
        for idx in Producto.__table__.indexes
    ), "sku debe ser UNIQUE"

    index_cols = {col.name for idx in Producto.__table__.indexes for col in idx.columns}
    # al menos categoria y estado indexados (sku ya único)
    assert "categoria" in index_cols, "falta índice en categoria"
    assert "estado" in index_cols, "falta índice en estado"


def test_modelo_producto_checks():
    """T02: checks de sku regex, nombre longitud, categoria enum, stock rango, estado enum."""
    from app.models.producto import Producto

    # obtener textos de CheckConstraint
    checks = [
        str(c.sqltext)
        for c in Producto.__table__.constraints
        if c.__class__.__name__ == "CheckConstraint"
    ]
    checks_text = " ".join(checks).lower()

    assert (
        "sku" in checks_text
        and "~" in checks_text
        or "regexp" in checks_text
        or "^[a-z0-9" in checks_text
    ), f"falta check SKU regex, checks={checks}"
    assert "categoria" in checks_text and "videojuego" in checks_text, (
        f"falta check categoria, checks={checks}"
    )
    assert "stock_inicial" in checks_text and "1000000" in checks_text, (
        f"falta check stock_inicial, checks={checks}"
    )
    assert (
        "estado" in checks_text
        and "activo" in checks_text
        and "inactivo" in checks_text
    ), f"falta check estado, checks={checks}"
    # nombre check
    assert "nombre" in checks_text or "length" in checks_text, (
        f"falta check nombre longitud, checks={checks}"
    )


def test_modelo_producto_es_singular_y_tabla_plural():
    """AGENTS.md: modelo singular Producto, tabla plural productos."""
    from app.models.producto import Producto

    assert Producto.__name__ == "Producto"
    assert Producto.__tablename__ == "productos"
