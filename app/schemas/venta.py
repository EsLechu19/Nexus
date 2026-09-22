"""Schemas Pydantic para ventas (RF-1, RNF-6)."""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, StrictInt, field_validator, model_validator


class ClienteVenta(BaseModel):
    """Cliente embebido en venta: nombre obligatorio 2-100, email opcional formato 002."""

    nombre: str
    email: Optional[str] = None

    @field_validator("nombre", mode="before")
    @classmethod
    def validar_nombre(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError("nombre debe ser texto")
        valor = v.strip()
        if len(valor) < 2 or len(valor) > 100:
            raise ValueError("nombre debe tener entre 2 y 100 caracteres")
        return valor

    @field_validator("email", mode="before")
    @classmethod
    def validar_email(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("email debe ser texto")
        # "" tras trim → 422 (mismo criterio 002)
        if v.strip() == "":
            raise ValueError("email no puede ser vacío")
        valor = v.strip().lower()
        if len(valor) > 254:
            raise ValueError("email debe tener máximo 254 caracteres")
        if valor.count("@") != 1:
            raise ValueError("email debe tener un @")
        local, dominio = valor.split("@", 1)
        if not local or len(local) > 64 or "." not in dominio:
            raise ValueError("email formato inválido")
        import re

        if not re.fullmatch(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$", valor):
            raise ValueError("email formato inválido")
        return valor


class VentaItemCreate(BaseModel):
    """Ítem del carrito: producto_codigo normalizado, cantidad StrictInt, precio Decimal 2 decimales."""

    producto_codigo: str
    cantidad: StrictInt
    precio_unitario: Decimal

    model_config = {"extra": "ignore"}

    @field_validator("producto_codigo", mode="before")
    @classmethod
    def validar_codigo(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError("producto_codigo debe ser texto")
        valor = v.strip().upper()
        import re

        if not re.fullmatch(r"^[A-Z0-9_-]{3,20}$", valor):
            raise ValueError(
                "producto_codigo debe tener 3-20 caracteres alfanuméricos, _ o -"
            )
        return valor

    @field_validator("cantidad", mode="before")
    @classmethod
    def validar_cantidad(cls, v: object) -> int:
        # StrictInt ya rechaza float y string, pero validamos rango
        if isinstance(v, bool):
            raise ValueError("cantidad debe ser entero")
        if not isinstance(v, int):
            raise ValueError("cantidad debe ser entero")
        if v < 1 or v > 1000000:
            raise ValueError("cantidad debe estar entre 1 y 1000000")
        return v

    @field_validator("precio_unitario", mode="before")
    @classmethod
    def validar_precio(cls, v: object) -> Decimal:
        # Rechaza float explícitamente (nunca float, RNF-6)
        if isinstance(v, bool):
            raise ValueError("precio_unitario debe ser Decimal")
        if isinstance(v, float):
            raise ValueError("precio_unitario debe ser Decimal, no float")
        # Acepta int, Decimal y string numérico (para JSON vía HTTP)
        # String se parsea a Decimal; si falla → 422
        if isinstance(v, str):
            valor_str = v.strip()
            if valor_str == "":
                raise ValueError("precio_unitario no puede ser vacío")
            try:
                v = Decimal(valor_str)
            except Exception:
                raise ValueError("precio_unitario debe ser Decimal")
        elif isinstance(v, int):
            # int sin decimales → Decimal exacto
            v = Decimal(str(v))
        elif isinstance(v, Decimal):
            pass
        else:
            raise ValueError("precio_unitario debe ser Decimal")
        # validar 2 decimales máximo y rango
        # Decimal con más de 2 decimales tiene exponent < -2
        if v.as_tuple().exponent < -2:  # type: ignore[operator]
            raise ValueError("precio_unitario debe tener máximo 2 decimales")
        if v < Decimal(0) or v > Decimal(1000000):
            raise ValueError("precio_unitario debe estar entre 0 y 1000000")
        return v


class VentaCreate(BaseModel):
    """Alta de venta: cliente + items 1-20, total/subtotal ignorados."""

    cliente: ClienteVenta
    items: list[VentaItemCreate]

    model_config = {"extra": "ignore"}

    @field_validator("items", mode="after")
    @classmethod
    def validar_items_tamano(cls, v: list[VentaItemCreate]) -> list[VentaItemCreate]:
        if len(v) < 1 or len(v) > 20:
            raise ValueError("items debe tener entre 1 y 20 elementos")
        return v

    @model_validator(mode="after")
    def validar_duplicado(self) -> "VentaCreate":
        codigos = [item.producto_codigo for item in self.items]
        if len(codigos) != len(set(codigos)):
            raise ValueError("SKU duplicado en el carrito tras normalización")
        return self


class VentaItemResponse(BaseModel):
    """Respuesta de ítem con subtotal."""

    producto_codigo: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal

    model_config = {"from_attributes": True}


class VentaResponse(BaseModel):
    """Respuesta de venta con id, created_at, cliente, items, total y movimientos_ids."""

    id: int
    created_at: str
    cliente: ClienteVenta
    items: list[VentaItemResponse]
    total: Decimal
    movimientos_ids: list[int]

    model_config = {"from_attributes": True}


class VentaListResponse(BaseModel):
    """Respuesta para listado."""

    id: int
    created_at: str
    cliente: ClienteVenta
    items: list[VentaItemResponse]
    total: Decimal
    movimientos_ids: list[int]

    model_config = {"from_attributes": True}
