"""Modelo VentaItem — tabla venta_items (RF-1, RF-2)."""

from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VentaItem(Base):
    """Línea del carrito de venta con referencia a movimiento salida."""

    __tablename__ = "venta_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    venta_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ventas.id", ondelete="RESTRICT"), nullable=False
    )

    producto_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False
    )

    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)

    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    movimiento_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("movimientos_inventario.id", ondelete="RESTRICT"),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "cantidad > 0 AND cantidad <= 1000000", name="ck_venta_items_cantidad"
        ),
        CheckConstraint(
            "precio_unitario >= 0 AND precio_unitario <= 1000000",
            name="ck_venta_items_precio",
        ),
        Index("ix_venta_items_movimiento_id", "movimiento_id", unique=True),
        Index("ix_venta_items_venta_id", "venta_id"),
        Index("ix_venta_items_producto_id", "producto_id"),
    )
