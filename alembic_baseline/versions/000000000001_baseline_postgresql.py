"""Esquema PostgreSQL inicial de Nexus para una base vacía."""

from alembic import op
import sqlalchemy as sa

revision = "000000000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "productos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sku", sa.String(length=20), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("categoria", sa.String(length=20), nullable=False),
        sa.Column("stock_inicial", sa.Integer(), server_default="0", nullable=False),
        sa.Column("stock_minimo", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "estado", sa.String(length=10), server_default="activo", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku", name="uq_productos_sku"),
        sa.CheckConstraint(
            "length(sku) BETWEEN 3 AND 20", name="ck_productos_sku_regex"
        ),
        sa.CheckConstraint(
            "length(trim(nombre)) BETWEEN 2 AND 100", name="ck_productos_nombre_length"
        ),
        sa.CheckConstraint(
            "categoria IN ('videojuego','consola','accesorio')",
            name="ck_productos_categoria",
        ),
        sa.CheckConstraint(
            "stock_inicial >= 0 AND stock_inicial <= 1000000",
            name="ck_productos_stock_inicial",
        ),
        sa.CheckConstraint(
            "stock_minimo >= 0 AND stock_minimo <= 1000000",
            name="ck_productos_stock_minimo",
        ),
        sa.CheckConstraint(
            "estado IN ('activo','inactivo')", name="ck_productos_estado"
        ),
    )
    op.create_index("ix_productos_sku", "productos", ["sku"], unique=True)
    op.create_index("ix_productos_categoria", "productos", ["categoria"])
    op.create_index("ix_productos_estado", "productos", ["estado"])

    op.create_table(
        "proveedores",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("codigo", sa.String(length=20), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=True),
        sa.Column("telefono", sa.String(length=20), nullable=True),
        sa.Column("direccion", sa.String(length=200), nullable=True),
        sa.Column(
            "estado", sa.String(length=10), server_default="activo", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo", name="uq_proveedores_codigo"),
        sa.CheckConstraint(
            "length(codigo) BETWEEN 3 AND 20", name="ck_proveedores_codigo_regex"
        ),
        sa.CheckConstraint(
            "length(trim(nombre)) BETWEEN 2 AND 100",
            name="ck_proveedores_nombre_length",
        ),
        sa.CheckConstraint(
            "email IS NULL OR length(email) <= 254", name="ck_proveedores_email"
        ),
        sa.CheckConstraint(
            "telefono IS NULL OR length(telefono) BETWEEN 7 AND 20",
            name="ck_proveedores_telefono",
        ),
        sa.CheckConstraint(
            "direccion IS NULL OR length(trim(direccion)) BETWEEN 5 AND 200",
            name="ck_proveedores_direccion",
        ),
        sa.CheckConstraint(
            "estado IN ('activo','inactivo')", name="ck_proveedores_estado"
        ),
    )
    op.create_index("ix_proveedores_codigo", "proveedores", ["codigo"], unique=True)
    op.create_index("ix_proveedores_nombre", "proveedores", ["nombre"])
    op.create_index("ix_proveedores_estado", "proveedores", ["estado"])

    op.create_table(
        "movimientos_inventario",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("producto_id", sa.Integer(), nullable=False),
        sa.Column("proveedor_id", sa.Integer(), nullable=True),
        sa.Column("tipo", sa.String(length=15), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("motivo", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["producto_id"], ["productos.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["proveedor_id"], ["proveedores.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "tipo IN ('entrada','salida','entrada_inicial')", name="ck_movimientos_tipo"
        ),
        sa.CheckConstraint(
            "cantidad > 0 AND cantidad <= 1000000", name="ck_movimientos_cantidad"
        ),
        sa.CheckConstraint(
            "motivo IS NULL OR length(trim(motivo)) BETWEEN 2 AND 200",
            name="ck_movimientos_motivo",
        ),
        sa.CheckConstraint(
            "(tipo = 'entrada' AND proveedor_id IS NOT NULL) OR (tipo != 'entrada')",
            name="ck_movimientos_proveedor_entrada",
        ),
    )
    for name, column in (
        ("producto_id", "producto_id"),
        ("proveedor_id", "proveedor_id"),
        ("tipo", "tipo"),
        ("created_at", "created_at"),
    ):
        op.create_index(f"ix_movimientos_{name}", "movimientos_inventario", [column])

    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=72), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)

    op.create_table(
        "ventas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("cliente_nombre", sa.String(length=100), nullable=False),
        sa.Column("cliente_email", sa.String(length=254), nullable=True),
        sa.Column("total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "length(trim(cliente_nombre)) BETWEEN 2 AND 100",
            name="ck_ventas_cliente_nombre",
        ),
        sa.CheckConstraint("total >= 0", name="ck_ventas_total"),
    )
    op.create_index("ix_ventas_created_at", "ventas", ["created_at"])

    op.create_table(
        "venta_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("venta_id", sa.Integer(), nullable=False),
        sa.Column("producto_id", sa.Integer(), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("subtotal", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("movimiento_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["venta_id"], ["ventas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["producto_id"], ["productos.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["movimiento_id"], ["movimientos_inventario.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "cantidad > 0 AND cantidad <= 1000000", name="ck_venta_items_cantidad"
        ),
        sa.CheckConstraint(
            "precio_unitario >= 0 AND precio_unitario <= 1000000",
            name="ck_venta_items_precio",
        ),
    )
    op.create_index(
        "ix_venta_items_movimiento_id", "venta_items", ["movimiento_id"], unique=True
    )
    op.create_index("ix_venta_items_venta_id", "venta_items", ["venta_id"])
    op.create_index("ix_venta_items_producto_id", "venta_items", ["producto_id"])


def downgrade() -> None:
    op.drop_table("venta_items")
    op.drop_table("ventas")
    op.drop_table("usuarios")
    op.drop_table("movimientos_inventario")
    op.drop_table("proveedores")
    op.drop_table("productos")
