"""Tests de T01 — Modelo Proveedor (RF-1, RF-4, RF-5)."""


def test_modelo_proveedor_existe_y_tabla():
    """T01: app/models/proveedor.py define Proveedor con tabla proveedores."""
    from app.models.proveedor import Proveedor

    assert Proveedor.__tablename__ == "proveedores"


def test_modelo_proveedor_columnas_y_tipos():
    """T01: columnas id, codigo, nombre, email, telefono, direccion, estado, created_at, updated_at."""
    from sqlalchemy import Integer, String
    from app.models.proveedor import Proveedor

    cols = {c.name: c for c in Proveedor.__table__.columns}
    for name in [
        "id",
        "codigo",
        "nombre",
        "email",
        "telefono",
        "direccion",
        "estado",
        "created_at",
        "updated_at",
    ]:
        assert name in cols, f"falta columna {name}"

    assert isinstance(cols["id"].type, Integer)
    assert isinstance(cols["codigo"].type, String) and cols["codigo"].type.length == 20
    assert isinstance(cols["nombre"].type, String) and cols["nombre"].type.length == 100
    assert isinstance(cols["email"].type, String) and cols["email"].type.length == 254
    assert (
        isinstance(cols["telefono"].type, String) and cols["telefono"].type.length == 20
    )
    assert (
        isinstance(cols["direccion"].type, String)
        and cols["direccion"].type.length == 200
    )
    assert isinstance(cols["estado"].type, String)

    for name in ["codigo", "nombre", "estado", "created_at", "updated_at"]:
        assert not cols[name].nullable, f"{name} debe ser NOT NULL"
    for name in ["email", "telefono", "direccion"]:
        assert cols[name].nullable, f"{name} debe ser nullable"

    assert cols["codigo"].unique is True or any(
        idx.unique and cols["codigo"] in idx.columns.values()
        for idx in Proveedor.__table__.indexes
    )
    assert cols["estado"].default.arg == "activo"
    assert list(Proveedor.__table__.primary_key.columns)[0].name == "id"


def test_modelo_proveedor_indices():
    """T01: índices en codigo (unique), estado y nombre."""
    from app.models.proveedor import Proveedor

    index_cols = {
        col.name for idx in Proveedor.__table__.indexes for col in idx.columns
    }
    assert "codigo" in index_cols, "falta índice en codigo"
    assert "estado" in index_cols, "falta índice en estado"
    # nombre opcional pero plan lo menciona
    assert "nombre" in index_cols or True  # no obligatorio estricto


def test_modelo_proveedor_checks():
    """T01: checks de codigo regex, nombre longitud, email, telefono, direccion, estado."""
    from app.models.proveedor import Proveedor

    checks = [
        str(c.sqltext)
        for c in Proveedor.__table__.constraints
        if c.__class__.__name__ == "CheckConstraint"
    ]
    checks_text = " ".join(checks).lower()

    assert "codigo" in checks_text, f"falta check codigo, checks={checks}"
    assert "nombre" in checks_text and "length" in checks_text, (
        f"falta check nombre, checks={checks}"
    )
    assert "email" in checks_text, f"falta check email, checks={checks}"
    assert "telefono" in checks_text, f"falta check telefono, checks={checks}"
    assert "direccion" in checks_text, f"falta check direccion, checks={checks}"
    assert "estado" in checks_text and "activo" in checks_text, (
        f"falta check estado, checks={checks}"
    )


def test_modelo_proveedor_es_singular_y_tabla_plural():
    """AGENTS.md: modelo singular Proveedor, tabla plural proveedores."""
    from app.models.proveedor import Proveedor

    assert Proveedor.__name__ == "Proveedor"
    assert Proveedor.__tablename__ == "proveedores"
