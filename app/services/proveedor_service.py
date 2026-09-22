"""Service de catálogo — lógica de negocio de Proveedor (RF-1)."""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.proveedor import Proveedor
from app.schemas.proveedor import ProveedorCreate, ProveedorUpdate


def crear_proveedor(db: Session, datos: ProveedorCreate) -> Proveedor:
    """Crea un proveedor con normalización y unicidad global (RF-1).

    Normaliza codigo (trim+upper), nombre (trim), email (trim+lower),
    telefono/direccion (trim), valida unicidad incluyendo inactivos,
    crea en estado activo. Captura carrera por IntegrityError -> 409.
    """
    codigo_norm = datos.codigo.strip().upper()
    nombre_norm = datos.nombre.strip()
    email_norm = datos.email.strip().lower() if datos.email is not None else None
    telefono_norm = datos.telefono.strip() if datos.telefono is not None else None
    direccion_norm = datos.direccion.strip() if datos.direccion is not None else None

    existente = db.query(Proveedor).filter(Proveedor.codigo == codigo_norm).first()
    if existente is not None:
        raise HTTPException(status_code=409, detail="Código ya existe")

    proveedor = Proveedor(
        codigo=codigo_norm,
        nombre=nombre_norm,
        email=email_norm,
        telefono=telefono_norm,
        direccion=direccion_norm,
        estado="activo",
    )

    try:
        db.add(proveedor)
        db.flush()
        db.commit()
        db.refresh(proveedor)
        return proveedor
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Código ya existe") from exc


def listar_activos(db: Session) -> list[Proveedor]:
    """Lista solo proveedores activos ordenados por código (RF-2)."""
    return (
        db.query(Proveedor)
        .filter(Proveedor.estado == "activo")
        .order_by(Proveedor.codigo)
        .all()
    )


def obtener_por_codigo(db: Session, codigo: str) -> Proveedor:
    """Obtiene proveedor por código normalizado, incluye inactivos (RF-3)."""
    codigo_norm = codigo.strip().upper()
    proveedor = db.query(Proveedor).filter(Proveedor.codigo == codigo_norm).first()
    if proveedor is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return proveedor


def actualizar_proveedor(db: Session, codigo: str, datos: ProveedorUpdate) -> Proveedor:
    """Edita nombre y contacto de proveedor activo (RF-4).

    Normaliza código path, valida existencia (404), inactivo (400),
    código inmutable (400 si distinto, ignora si igual), ignora estado,
    y actualiza solo campos explícitamente enviados: null borra, ausente no cambia.
    """
    codigo_norm = codigo.strip().upper()
    proveedor = db.query(Proveedor).filter(Proveedor.codigo == codigo_norm).first()
    if proveedor is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    if proveedor.estado == "inactivo":
        raise HTTPException(status_code=400, detail="Proveedor inactivo no editable")

    if datos.codigo is not None:
        codigo_payload_norm = datos.codigo.strip().upper()
        if codigo_payload_norm != codigo_norm:
            raise HTTPException(status_code=400, detail="Código inmutable")

    # Actualizar solo campos explícitamente enviados (model_fields_set)
    if "nombre" in datos.model_fields_set and datos.nombre is not None:
        proveedor.nombre = datos.nombre.strip()
    if "email" in datos.model_fields_set:
        # None borra, string actualiza (ya normalizado a lower en schema)
        proveedor.email = (
            datos.email.strip().lower() if datos.email is not None else None
        )
    if "telefono" in datos.model_fields_set:
        proveedor.telefono = (
            datos.telefono.strip() if datos.telefono is not None else None
        )
    if "direccion" in datos.model_fields_set:
        proveedor.direccion = (
            datos.direccion.strip() if datos.direccion is not None else None
        )

    db.commit()
    db.refresh(proveedor)
    return proveedor


def baja_proveedor(db: Session, codigo: str) -> Proveedor:
    """Da de baja lógica proveedor activo (RF-5).

    Normaliza código, valida existencia (404) y que no esté ya inactivo (400).
    Marca estado a inactivo sin borrar (RNF-1), permite con cualquier contacto.
    """
    codigo_norm = codigo.strip().upper()
    proveedor = db.query(Proveedor).filter(Proveedor.codigo == codigo_norm).first()
    if proveedor is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    if proveedor.estado == "inactivo":
        raise HTTPException(status_code=400, detail="Proveedor ya dado de baja")

    proveedor.estado = "inactivo"
    db.commit()
    db.refresh(proveedor)
    return proveedor
