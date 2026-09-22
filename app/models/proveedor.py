"""Modelo Proveedor — tabla proveedores (RF-1, RF-4, RF-5)."""

from datetime import datetime

from sqlalchemy import CheckConstraint, String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Proveedor(Base):
    """Proveedor externo para reposición de stock. Trazabilidad y unicidad de código."""

    __tablename__ = "proveedores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    codigo: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True
    )

    nombre: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    email: Mapped[str | None] = mapped_column(String(254), nullable=True)

    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)

    direccion: Mapped[str | None] = mapped_column(String(200), nullable=True)

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
            "length(codigo) BETWEEN 3 AND 20 /* codigo ~ '^[A-Z0-9_-]{3,20}$' */",
            name="ck_proveedores_codigo_regex",
        ),
        CheckConstraint(
            "length(trim(nombre)) BETWEEN 2 AND 100",
            name="ck_proveedores_nombre_length",
        ),
        CheckConstraint(
            "email IS NULL OR length(email) <= 254 /* email ~ '^[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}$' */",
            name="ck_proveedores_email",
        ),
        CheckConstraint(
            "telefono IS NULL OR length(telefono) BETWEEN 7 AND 20 /* telefono digitos 7-15 */",
            name="ck_proveedores_telefono",
        ),
        CheckConstraint(
            "direccion IS NULL OR length(trim(direccion)) BETWEEN 5 AND 200",
            name="ck_proveedores_direccion",
        ),
        CheckConstraint(
            "estado IN ('activo','inactivo')", name="ck_proveedores_estado"
        ),
    )
