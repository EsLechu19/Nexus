"""Service de catálogo — lógica de negocio de Producto (RF-1, RF-2, RF-3)."""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.movimiento_inventario import MovimientoInventario
from app.models.producto import Producto
from app.schemas.producto import ProductoCreate, ProductoUpdate


def crear_producto(db: Session, datos: ProductoCreate) -> Producto:
    """Crea un producto con normalización y unicidad global (RF-1).

    Normaliza sku (trim+upper) y categoria (trim+lower), valida unicidad
    incluyendo inactivos, crea producto en estado activo y genera traza
    append-only si stock_inicial > 0. Captura carrera por IntegrityError -> 409.
    """
    sku_norm = datos.sku.strip().upper()
    categoria_norm = datos.categoria.strip().lower()
    nombre_norm = datos.nombre.strip()
    stock = datos.stock_inicial if datos.stock_inicial is not None else 0
    stock_minimo = datos.stock_minimo if datos.stock_minimo is not None else 0

    # Unicidad global incluyendo inactivos (RNF-3)
    existente = db.query(Producto).filter(Producto.sku == sku_norm).first()
    if existente is not None:
        raise HTTPException(status_code=409, detail="SKU ya existe")

    producto = Producto(
        sku=sku_norm,
        nombre=nombre_norm,
        categoria=categoria_norm,
        stock_inicial=stock,
        stock_minimo=stock_minimo,
        estado="activo",
    )

    try:
        db.add(producto)
        # flush para obtener id antes de crear movimiento
        db.flush()

        if stock > 0:
            movimiento = MovimientoInventario(
                producto_id=producto.id,
                tipo="entrada_inicial",
                cantidad=stock,
            )
            db.add(movimiento)

        db.commit()
        db.refresh(producto)
        return producto
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="SKU ya existe") from exc


def listar_activos(db: Session) -> list[Producto]:
    """Lista solo productos activos (RF-2)."""
    return (
        db.query(Producto)
        .filter(Producto.estado == "activo")
        .order_by(Producto.sku)
        .all()
    )


def obtener_por_sku(db: Session, sku: str) -> Producto:
    """Obtiene producto por SKU normalizado, incluye inactivos (RF-3).

    Normaliza SKU con trim+upper. Si no existe, lanza 404.
    """
    sku_norm = sku.strip().upper()
    producto = db.query(Producto).filter(Producto.sku == sku_norm).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


def actualizar_producto(db: Session, sku: str, datos: ProductoUpdate) -> Producto:
    """Edita nombre y/o categoria de producto activo (RF-4).

    Normaliza SKU path con trim+upper. Valida existencia (404),
    estado inactivo (400), sku inmutable (400 si distinto, ignora si igual),
    y actualiza solo campos permitidos. Ignora stock_inicial/estado extra.
    """
    sku_norm = sku.strip().upper()
    producto = db.query(Producto).filter(Producto.sku == sku_norm).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if producto.estado == "inactivo":
        raise HTTPException(status_code=400, detail="Producto inactivo no editable")

    # Inmutabilidad de SKU: si payload trae sku distinto -> 400, si igual -> ignora
    if datos.sku is not None:
        sku_payload_norm = datos.sku.strip().upper()
        if sku_payload_norm != sku_norm:
            raise HTTPException(status_code=400, detail="SKU inmutable")
        # si es igual, se ignora

    # Actualizar solo campos permitidos
    if datos.nombre is not None:
        producto.nombre = datos.nombre.strip()
    if datos.categoria is not None:
        producto.categoria = datos.categoria.strip().lower()
    if "stock_minimo" in datos.model_fields_set and datos.stock_minimo is not None:
        # stock_minimo ya validado en schema, solo actualizar si se envió explícitamente
        producto.stock_minimo = datos.stock_minimo
    elif "stock_minimo" in datos.model_fields_set and datos.stock_minimo is None:
        # Si se envía null explícitamente, se ignora (no se borra, ya que es NOT NULL)
        pass

    db.commit()
    db.refresh(producto)
    return producto


def baja_producto(db: Session, sku: str) -> Producto:
    """Da de baja lógica producto activo (RF-5).

    Normaliza SKU, valida existencia (404) y que no esté ya inactivo (400).
    Marca estado a inactivo sin borrar (RNF-1), permite cualquier stock_inicial.
    """
    sku_norm = sku.strip().upper()
    producto = db.query(Producto).filter(Producto.sku == sku_norm).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if producto.estado == "inactivo":
        raise HTTPException(status_code=400, detail="Producto ya dado de baja")

    producto.estado = "inactivo"
    db.commit()
    db.refresh(producto)
    return producto
