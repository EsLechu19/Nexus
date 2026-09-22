"""Schemas Pydantic para movimientos de inventario (RF-1, RF-2, RF-3, RF-4)."""

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, field_validator


def _validar_codigo(v: object) -> str:
    if not isinstance(v, str):
        raise ValueError("codigo debe ser texto")
    valor = v.strip().upper()
    if len(valor) < 3 or len(valor) > 20:
        raise ValueError("codigo debe tener entre 3 y 20 caracteres")
    import re

    if not re.fullmatch(r"[A-Z0-9_-]+", valor):
        raise ValueError("codigo solo permite letras, números, guion y guion bajo")
    return valor


def _validar_motivo(v: object) -> Optional[str]:
    if v is None:
        return None
    if not isinstance(v, str):
        raise ValueError("motivo debe ser texto")
    valor = v.strip()
    if valor == "":
        raise ValueError("motivo no puede ser vacío")
    if len(valor) < 2 or len(valor) > 200:
        raise ValueError("motivo debe tener entre 2 y 200 caracteres")
    if "\n" in valor or "\r" in valor:
        raise ValueError("motivo no puede contener saltos de línea")
    return valor


class MovimientoCreateEntrada(BaseModel):
    """Alta de entrada: producto + proveedor + cantidad + motivo opcional."""

    producto_codigo: Annotated[str, Field(min_length=3, max_length=20)]
    proveedor_codigo: Annotated[str, Field(min_length=3, max_length=20)]
    cantidad: Annotated[int, Field(ge=1, le=1000000, strict=True)]
    motivo: Annotated[Optional[str], Field(default=None)] = None

    @field_validator("producto_codigo", mode="before")
    @classmethod
    def validar_producto_codigo(cls, v: object) -> str:
        return _validar_codigo(v)

    @field_validator("proveedor_codigo", mode="before")
    @classmethod
    def validar_proveedor_codigo(cls, v: object) -> str:
        return _validar_codigo(v)

    @field_validator("motivo", mode="before")
    @classmethod
    def validar_motivo(cls, v: object) -> Optional[str]:
        return _validar_motivo(v)


class MovimientoCreateSalida(BaseModel):
    """Alta de salida: producto + cantidad + motivo opcional, sin proveedor."""

    producto_codigo: Annotated[str, Field(min_length=3, max_length=20)]
    cantidad: Annotated[int, Field(ge=1, le=1000000, strict=True)]
    motivo: Annotated[Optional[str], Field(default=None)] = None

    model_config = {"extra": "forbid"}

    @field_validator("producto_codigo", mode="before")
    @classmethod
    def validar_producto_codigo(cls, v: object) -> str:
        return _validar_codigo(v)

    @field_validator("motivo", mode="before")
    @classmethod
    def validar_motivo(cls, v: object) -> Optional[str]:
        return _validar_motivo(v)


class MovimientoResponse(BaseModel):
    """Respuesta de movimiento."""

    id: int
    producto_codigo: str
    proveedor_codigo: Optional[str] = None
    tipo: Literal["entrada", "salida", "entrada_inicial"]
    cantidad: int
    motivo: Optional[str] = None
    fecha: str
    stock_actual: Optional[int] = None

    model_config = {"from_attributes": True}


class HistorialQuery(BaseModel):
    """Filtros para historial."""

    producto_codigo: Optional[str] = None
    tipo: Optional[Literal["entrada", "salida", "entrada_inicial"]] = None

    @field_validator("producto_codigo", mode="before")
    @classmethod
    def validar_producto_codigo(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        return _validar_codigo(v)


class StockResponse(BaseModel):
    """Respuesta de stock actual."""

    codigo: str
    nombre: str
    stock_inicial: int
    entradas: int
    salidas: int
    stock_actual: int

    model_config = {"from_attributes": True}
