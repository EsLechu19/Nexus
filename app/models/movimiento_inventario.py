"""Modelo MovimientoInventario — tabla movimientos_inventario (RF-1 traza inicial, append-only)."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Integer,
    DateTime,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MovimientoInventario(Base):
    """Traza inmutable de movimientos de inventario. Append-only."""

    __tablename__ = "movimientos_inventario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    producto_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("productos.id", ondelete="RESTRICT"),
        nullable=False,
    )

    proveedor_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("proveedores.id", ondelete="RESTRICT"),
        nullable=True,
    )

    tipo: Mapped[str] = mapped_column(String(15), nullable=False)

    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)

    motivo: Mapped[str | None] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "tipo IN ('entrada','salida','entrada_inicial')",
            name="ck_movimientos_tipo",
        ),
        CheckConstraint(
            "cantidad > 0 AND cantidad <= 1000000",
            name="ck_movimientos_cantidad",
        ),
        CheckConstraint(
            "motivo IS NULL OR length(trim(motivo)) BETWEEN 2 AND 200",
            name="ck_movimientos_motivo",
        ),
        CheckConstraint(
            "(tipo = 'entrada' AND proveedor_id IS NOT NULL) OR (tipo != 'entrada')",
            name="ck_movimientos_proveedor_entrada",
        ),
        Index("ix_movimientos_producto_id", "producto_id"),
        Index("ix_movimientos_proveedor_id", "proveedor_id"),
        Index("ix_movimientos_tipo", "tipo"),
        Index("ix_movimientos_created_at", "created_at"),
    )
