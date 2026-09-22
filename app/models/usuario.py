"""Modelo Usuario — tabla usuarios (RF-4, RNF-1, RNF-3)."""

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Usuario(Base):
    """Usuario con email único y password hasheada. Solo email+hash en MVP."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    email: Mapped[str] = mapped_column(String(254), nullable=False)

    password_hash: Mapped[str] = mapped_column(String(72), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("ix_usuarios_email", "email", unique=True),)
