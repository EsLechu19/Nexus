"""Schemas para consulta de stock (RF-1)."""

from pydantic import BaseModel, field_validator


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


class StockResponse(BaseModel):
    """Respuesta de stock con alerta."""

    codigo: str
    nombre: str
    stock_inicial: int
    stock_minimo: int
    entradas: int
    salidas: int
    stock_actual: int
    alerta: bool

    model_config = {"from_attributes": True}


class StockQuery(BaseModel):
    """Query para stock por código."""

    codigo: str

    @field_validator("codigo", mode="before")
    @classmethod
    def validar_codigo(cls, v: object) -> str:
        return _validar_codigo(v)


class StockListResponse(BaseModel):
    """Respuesta para listado global (alias de StockResponse)."""

    codigo: str
    nombre: str
    stock_inicial: int
    stock_minimo: int
    entradas: int
    salidas: int
    stock_actual: int
    alerta: bool

    model_config = {"from_attributes": True}
