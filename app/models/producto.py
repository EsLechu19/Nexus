"""Modelo Producto — tabla productos (RF-1, RF-4, RF-5)."""

from datetime import datetime

from sqlalchemy import CheckConstraint, String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Producto(Base):
    """Producto del catálogo. Trazabilidad y unicidad de SKU."""

    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    sku: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True
    )

    nombre: Mapped[str] = mapped_column(String(100), nullable=False)

    categoria: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    stock_inicial: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    stock_minimo: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    estado: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="activo",
        server_default="activo",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "length(sku) BETWEEN 3 AND 20 /* sku ~ '^[A-Z0-9_-]{3,20}$' */",
            name="ck_productos_sku_regex",
        ),
        CheckConstraint(
            "length(trim(nombre)) BETWEEN 2 AND 100", name="ck_productos_nombre_length"
        ),
        CheckConstraint(
            "categoria IN ('videojuego','consola','accesorio')",
            name="ck_productos_categoria",
        ),
        CheckConstraint(
            "stock_inicial >= 0 AND stock_inicial <= 1000000",
            name="ck_productos_stock_inicial",
        ),
        CheckConstraint(
            "stock_minimo >= 0 AND stock_minimo <= 1000000",
            name="ck_productos_stock_minimo",
        ),
        CheckConstraint("estado IN ('activo','inactivo')", name="ck_productos_estado"),
    )
