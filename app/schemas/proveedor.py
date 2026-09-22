"""Schemas Pydantic para catálogo de proveedores (RF-1, RF-4)."""

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

EstadoLiteral = Literal["activo", "inactivo"]


class ProveedorCreate(BaseModel):
    """Alta de proveedor. Validación sintáctica sin acceso a BD."""

    codigo: Annotated[str, Field(min_length=3, max_length=20)]
    nombre: Annotated[str, Field(min_length=2, max_length=100)]
    email: Annotated[Optional[str], Field(default=None)] = None
    telefono: Annotated[Optional[str], Field(default=None)] = None
    direccion: Annotated[Optional[str], Field(default=None)] = None

    @field_validator("codigo", mode="before")
    @classmethod
    def validar_codigo(cls, v: object) -> str:
        """Trim y valida 3-20 alfanumérico _- , retorna mayúsculas."""
        if not isinstance(v, str):
            raise ValueError("codigo debe ser texto")
        valor = v.strip()
        if len(valor) < 3 or len(valor) > 20:
            raise ValueError("codigo debe tener entre 3 y 20 caracteres")
        import re

        if not re.fullmatch(r"[A-Za-z0-9_-]+", valor):
            raise ValueError("codigo solo permite letras, números, guion y guion bajo")
        return valor.upper()

    @field_validator("nombre", mode="before")
    @classmethod
    def validar_nombre(cls, v: object) -> str:
        """Trim y valida 2-100."""
        if not isinstance(v, str):
            raise ValueError("nombre debe ser texto")
        valor = v.strip()
        if len(valor) < 2 or len(valor) > 100:
            raise ValueError("nombre debe tener entre 2 y 100 caracteres")
        return valor

    @field_validator("email", mode="before")
    @classmethod
    def validar_email(cls, v: object) -> Optional[str]:
        """Trim+lower y valida formato, None/ausente -> None, '' -> 422."""
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("email debe ser texto")
        valor = v.strip()
        if valor == "":
            raise ValueError("email no puede ser vacío")
        valor = valor.lower()
        if len(valor) > 254:
            raise ValueError("email debe tener máximo 254 caracteres")
        import re

        if not re.fullmatch(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", valor):
            raise ValueError("email debe tener formato válido")
        return valor

    @field_validator("telefono", mode="before")
    @classmethod
    def validar_telefono(cls, v: object) -> Optional[str]:
        """Trim y valida 7-15 dígitos, + solo inicio, espacios/guiones/() permitidos."""
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("telefono debe ser texto")
        valor = v.strip()
        if valor == "":
            raise ValueError("telefono no puede ser vacío")
        # No letras
        import re

        if re.search(r"[A-Za-z]", valor):
            raise ValueError("telefono no puede contener letras")
        # + solo al inicio
        if "+" in valor and not valor.startswith("+"):
            raise ValueError("telefono solo puede tener + al inicio")
        if valor.count("+") > 1:
            raise ValueError("telefono solo puede tener un +")
        # Contar dígitos
        digitos = re.sub(r"\D", "", valor)
        if len(digitos) < 7 or len(digitos) > 15:
            raise ValueError("telefono debe tener entre 7 y 15 dígitos")
        # Caracteres permitidos
        if not re.fullmatch(r"[0-9+\s\(\)-]+", valor):
            raise ValueError(
                "telefono solo permite dígitos, +, espacios, guiones y paréntesis"
            )
        return valor

    @field_validator("direccion", mode="before")
    @classmethod
    def validar_direccion(cls, v: object) -> Optional[str]:
        """Trim y valida 5-200, sin control chars."""
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("direccion debe ser texto")
        valor = v.strip()
        if valor == "":
            raise ValueError("direccion no puede ser vacío")
        if len(valor) < 5 or len(valor) > 200:
            raise ValueError("direccion debe tener entre 5 y 200 caracteres")
        if any(ord(c) < 32 for c in valor) and "\n" not in valor and "\r" not in valor:
            # Permitir que el validador rechace \n si se considera control
            pass
        # Rechazar \n explícitamente como control
        if "\n" in valor or "\r" in valor:
            raise ValueError("direccion no puede contener saltos de línea")
        return valor


class ProveedorUpdate(BaseModel):
    """Edición parcial de proveedor. Al menos un campo requerido."""

    nombre: Annotated[
        Optional[str], Field(default=None, min_length=2, max_length=100)
    ] = None
    email: Annotated[Optional[str], Field(default=None)] = None
    telefono: Annotated[Optional[str], Field(default=None)] = None
    direccion: Annotated[Optional[str], Field(default=None)] = None
    codigo: Annotated[Optional[str], Field(default=None)] = None

    @field_validator("nombre", mode="before")
    @classmethod
    def validar_nombre_update(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("nombre debe ser texto")
        valor = v.strip()
        if valor == "":
            raise ValueError("nombre no puede ser vacío")
        if len(valor) < 2 or len(valor) > 100:
            raise ValueError("nombre debe tener entre 2 y 100 caracteres")
        return valor

    @field_validator("email", mode="before")
    @classmethod
    def validar_email_update(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("email debe ser texto")
        valor = v.strip()
        if valor == "":
            raise ValueError("email no puede ser vacío")
        valor = valor.lower()
        if len(valor) > 254:
            raise ValueError("email debe tener máximo 254 caracteres")
        import re

        if not re.fullmatch(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", valor):
            raise ValueError("email debe tener formato válido")
        return valor

    @field_validator("telefono", mode="before")
    @classmethod
    def validar_telefono_update(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("telefono debe ser texto")
        valor = v.strip()
        if valor == "":
            raise ValueError("telefono no puede ser vacío")
        import re

        if re.search(r"[A-Za-z]", valor):
            raise ValueError("telefono no puede contener letras")
        if "+" in valor and not valor.startswith("+"):
            raise ValueError("telefono solo puede tener + al inicio")
        if valor.count("+") > 1:
            raise ValueError("telefono solo puede tener un +")
        digitos = re.sub(r"\D", "", valor)
        if len(digitos) < 7 or len(digitos) > 15:
            raise ValueError("telefono debe tener entre 7 y 15 dígitos")
        if not re.fullmatch(r"[0-9+\s\(\)-]+", valor):
            raise ValueError(
                "telefono solo permite dígitos, +, espacios, guiones y paréntesis"
            )
        return valor

    @field_validator("direccion", mode="before")
    @classmethod
    def validar_direccion_update(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("direccion debe ser texto")
        valor = v.strip()
        if valor == "":
            raise ValueError("direccion no puede ser vacío")
        if len(valor) < 5 or len(valor) > 200:
            raise ValueError("direccion debe tener entre 5 y 200 caracteres")
        if "\n" in valor or "\r" in valor:
            raise ValueError("direccion no puede contener saltos de línea")
        return valor

    @field_validator("codigo", mode="before")
    @classmethod
    def validar_codigo_update(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("codigo debe ser texto")
        valor = v.strip()
        if len(valor) < 3 or len(valor) > 20:
            raise ValueError("codigo debe tener entre 3 y 20 caracteres")
        import re

        if not re.fullmatch(r"[A-Za-z0-9_-]+", valor):
            raise ValueError("codigo solo permite letras, números, guion y guion bajo")
        return valor.upper()

    @model_validator(mode="after")
    def validar_al_menos_un_campo(self) -> "ProveedorUpdate":
        """Exige al menos uno de nombre/email/telefono/direccion (codigo/estado no cuentan)."""
        if not any(
            field in self.model_fields_set
            for field in ["nombre", "email", "telefono", "direccion"]
        ):
            raise ValueError(
                "debe proporcionar al menos nombre, email, telefono o direccion"
            )
        return self

    model_config = {"extra": "ignore"}


class ProveedorResponse(BaseModel):
    """Respuesta de proveedor. No expone modelo SQLAlchemy."""

    codigo: str
    nombre: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    estado: EstadoLiteral

    model_config = {"from_attributes": True}


class ProveedorListResponse(BaseModel):
    """Respuesta para listado (RF-2): sin estado."""

    codigo: str
    nombre: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None

    model_config = {"from_attributes": True}
