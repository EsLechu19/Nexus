"""Modelo Venta — tabla ventas (RF-1, RF-2, RNF-3)."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Venta(Base):
    """Cabecera de venta con cliente embebido y total derivado. Append-only."""

    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    cliente_nombre: Mapped[str] = mapped_column(String(100), nullable=False)

    cliente_email: Mapped[str | None] = mapped_column(String(254), nullable=True)

    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "length(trim(cliente_nombre)) BETWEEN 2 AND 100",
            name="ck_ventas_cliente_nombre",
        ),
        CheckConstraint("total >= 0", name="ck_ventas_total"),
        Index("ix_ventas_created_at", "created_at"),
    )
