"""Schemas Pydantic para catálogo de productos (RF-1, RF-2, RF-4)."""

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


CategoriaLiteral = Literal["videojuego", "consola", "accesorio"]
EstadoLiteral = Literal["activo", "inactivo"]


class ProductoCreate(BaseModel):
    """Alta de producto. Validación sintáctica sin acceso a BD."""

    sku: Annotated[str, Field(min_length=3, max_length=20)]
    nombre: Annotated[str, Field(min_length=2, max_length=100)]
    categoria: CategoriaLiteral
    stock_inicial: Annotated[Optional[int], Field(default=0, ge=0, le=1000000)] = 0
    stock_minimo: Annotated[Optional[int], Field(default=0, ge=0, le=1000000)] = 0

    @field_validator("sku", mode="before")
    @classmethod
    def validar_sku(cls, v: object) -> str:
        """Trim y valida formato alfanumérico _- y longitud 3-20."""
        if not isinstance(v, str):
            raise ValueError("sku debe ser texto")
        valor = v.strip()
        if len(valor) < 3 or len(valor) > 20:
            raise ValueError("sku debe tener entre 3 y 20 caracteres")
        # solo alfanumérico, guion y guion bajo
        import re

        if not re.fullmatch(r"[A-Za-z0-9_-]+", valor):
            raise ValueError("sku solo permite letras, números, guion y guion bajo")
        return valor

    @field_validator("nombre", mode="before")
    @classmethod
    def validar_nombre(cls, v: object) -> str:
        """Trim y valida 2-100 tras trim, no vacío."""
        if not isinstance(v, str):
            raise ValueError("nombre debe ser texto")
        valor = v.strip()
        if len(valor) < 2 or len(valor) > 100:
            raise ValueError("nombre debe tener entre 2 y 100 caracteres")
        return valor

    @field_validator("categoria", mode="before")
    @classmethod
    def validar_categoria(cls, v: object) -> str:
        """Trim + lower y valida enum."""
        if not isinstance(v, str):
            raise ValueError("categoria debe ser texto")
        valor = v.strip().lower()
        if valor not in ("videojuego", "consola", "accesorio"):
            raise ValueError("categoria debe ser videojuego, consola o accesorio")
        return valor

    @field_validator("stock_inicial", mode="before")
    @classmethod
    def validar_stock(cls, v: object) -> int:
        """Opcional: None/omitido -> 0, solo int 0-1_000_000, rechaza decimal/string."""
        if v is None:
            return 0
        if isinstance(v, bool):
            raise ValueError("stock_inicial debe ser entero")
        if not isinstance(v, int):
            raise ValueError("stock_inicial debe ser entero")
        if v < 0 or v > 1000000:
            raise ValueError("stock_inicial debe estar entre 0 y 1000000")
        return v

    @field_validator("stock_minimo", mode="before")
    @classmethod
    def validar_stock_minimo(cls, v: object) -> int:
        """Opcional: None/omitido -> 0, solo int 0-1_000_000."""
        if v is None:
            return 0
        if isinstance(v, bool):
            raise ValueError("stock_minimo debe ser entero")
        if not isinstance(v, int):
            raise ValueError("stock_minimo debe ser entero")
        if v < 0 or v > 1000000:
            raise ValueError("stock_minimo debe estar entre 0 y 1000000")
        return v


class ProductoUpdate(BaseModel):
    """Edición parcial de producto. Al menos un campo requerido."""

    nombre: Annotated[
        Optional[str], Field(default=None, min_length=2, max_length=100)
    ] = None
    categoria: Optional[CategoriaLiteral] = None
    sku: Annotated[Optional[str], Field(default=None)] = None
    stock_minimo: Annotated[Optional[int], Field(default=None, ge=0, le=1000000)] = None

    @field_validator("nombre", mode="before")
    @classmethod
    def validar_nombre_update(cls, v: object) -> Optional[str]:
        """Trim y valida 2-100 si se proporciona."""
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("nombre debe ser texto")
        valor = v.strip()
        if len(valor) < 2 or len(valor) > 100:
            raise ValueError("nombre debe tener entre 2 y 100 caracteres")
        return valor

    @field_validator("categoria", mode="before")
    @classmethod
    def validar_categoria_update(cls, v: object) -> Optional[str]:
        """Trim + lower y valida enum si se proporciona."""
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("categoria debe ser texto")
        valor = v.strip().lower()
        if valor not in ("videojuego", "consola", "accesorio"):
            raise ValueError("categoria debe ser videojuego, consola o accesorio")
        return valor

    @field_validator("sku", mode="before")
    @classmethod
    def validar_sku_update(cls, v: object) -> Optional[str]:
        """Trim y valida formato si se proporciona (para inmutabilidad)."""
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("sku debe ser texto")
        valor = v.strip()
        if len(valor) < 3 or len(valor) > 20:
            raise ValueError("sku debe tener entre 3 y 20 caracteres")
        import re

        if not re.fullmatch(r"[A-Za-z0-9_-]+", valor):
            raise ValueError("sku solo permite letras, números, guion y guion bajo")
        return valor

    @field_validator("stock_minimo", mode="before")
    @classmethod
    def validar_stock_minimo_update(cls, v: object) -> Optional[int]:
        """Opcional: None -> None (no cambia), solo int 0-1_000_000."""
        if v is None:
            return None
        if isinstance(v, bool):
            raise ValueError("stock_minimo debe ser entero")
        if not isinstance(v, int):
            raise ValueError("stock_minimo debe ser entero")
        if v < 0 or v > 1000000:
            raise ValueError("stock_minimo debe estar entre 0 y 1000000")
        return v

    @model_validator(mode="after")
    def validar_al_menos_un_campo(self) -> "ProductoUpdate":
        """Exige al menos un campo editable (nombre, categoria o stock_minimo). Sku no cuenta."""
        if self.nombre is None and self.categoria is None and self.stock_minimo is None:
            raise ValueError(
                "debe proporcionar al menos nombre, categoria o stock_minimo"
            )
        return self


class ProductoResponse(BaseModel):
    """Respuesta de producto. No expone modelo SQLAlchemy."""

    sku: str
    nombre: str
    categoria: CategoriaLiteral
    stock_inicial: int
    stock_minimo: int = 0
    estado: EstadoLiteral

    model_config = {"from_attributes": True}


class ProductoListResponse(BaseModel):
    """Respuesta para listado (RF-2): sin estado."""

    sku: str
    nombre: str
    categoria: CategoriaLiteral
    stock_inicial: int
    stock_minimo: int = 0

    model_config = {"from_attributes": True}
