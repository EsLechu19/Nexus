"""Service de movimientos — lógica de negocio (RF-1, RF-2, RF-3, RF-4)."""

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.movimiento_inventario import MovimientoInventario
from app.models.producto import Producto
from app.models.proveedor import Proveedor
from app.schemas.movimiento import MovimientoCreateEntrada, MovimientoCreateSalida


def _get_producto_activo(db: Session, codigo: str) -> Producto:
    codigo_norm = codigo.strip().upper()
    producto = db.query(Producto).filter(Producto.sku == codigo_norm).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if producto.estado != "activo":
        raise HTTPException(status_code=400, detail="Producto inactivo")
    return producto


def _get_proveedor_activo(db: Session, codigo: str) -> Proveedor:
    codigo_norm = codigo.strip().upper()
    proveedor = db.query(Proveedor).filter(Proveedor.codigo == codigo_norm).first()
    if proveedor is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    if proveedor.estado != "activo":
        raise HTTPException(status_code=400, detail="Proveedor inactivo")
    return proveedor


def _calcular_stock_actual(db: Session, producto_id: int, stock_inicial: int) -> dict:
    """Calcula entradas, salidas y stock_actual para un producto."""
    entradas = (
        db.query(func.coalesce(func.sum(MovimientoInventario.cantidad), 0))
        .filter(
            MovimientoInventario.producto_id == producto_id,
            MovimientoInventario.tipo == "entrada",
        )
        .scalar()
    )
    salidas = (
        db.query(func.coalesce(func.sum(MovimientoInventario.cantidad), 0))
        .filter(
            MovimientoInventario.producto_id == producto_id,
            MovimientoInventario.tipo == "salida",
        )
        .scalar()
    )
    stock_actual = stock_inicial + int(entradas or 0) - int(salidas or 0)
    return {
        "entradas": int(entradas or 0),
        "salidas": int(salidas or 0),
        "stock_actual": stock_actual,
    }


def registrar_entrada(
    db: Session, datos: MovimientoCreateEntrada
) -> MovimientoInventario:
    """Registra entrada de stock (RF-1)."""
    # Normalización ya hecha en schema, pero re-normalizamos por seguridad
    producto_codigo_norm = datos.producto_codigo.strip().upper()
    proveedor_codigo_norm = datos.proveedor_codigo.strip().upper()
    motivo_norm = datos.motivo.strip() if datos.motivo is not None else None

    # Validación con bloqueo pesimista del producto para evitar carrera con baja
    # En SQLite FOR UPDATE no existe, se usa SELECT normal; en Postgres sería FOR UPDATE
    producto = _get_producto_activo(db, producto_codigo_norm)
    proveedor = _get_proveedor_activo(db, proveedor_codigo_norm)

    # Para SQLite, el bloqueo se simula con la transacción; en Postgres usaríamos with_for_update()
    try:
        # Intentar SELECT FOR UPDATE si el dialecto lo soporta
        db.query(Producto).filter(Producto.id == producto.id).with_for_update().first()  # type: ignore[attr-defined]
    except Exception:
        pass  # SQLite no soporta FOR UPDATE, se ignora

    movimiento = MovimientoInventario(
        producto_id=producto.id,
        proveedor_id=proveedor.id,
        tipo="entrada",
        cantidad=datos.cantidad,
        motivo=motivo_norm,
    )
    db.add(movimiento)
    db.commit()
    db.refresh(movimiento)
    return movimiento


def registrar_salida(
    db: Session, datos: MovimientoCreateSalida
) -> MovimientoInventario:
    """Registra salida de stock (RF-2) con validación de stock suficiente."""
    producto_codigo_norm = datos.producto_codigo.strip().upper()
    motivo_norm = datos.motivo.strip() if datos.motivo is not None else None

    producto = _get_producto_activo(db, producto_codigo_norm)

    # Bloqueo pesimista para serializar salidas concurrentes
    try:
        db.query(Producto).filter(Producto.id == producto.id).with_for_update().first()  # type: ignore[attr-defined]
    except Exception:
        pass

    # Calcular stock actual y validar suficiencia
    calc = _calcular_stock_actual(db, producto.id, producto.stock_inicial)
    if datos.cantidad > calc["stock_actual"]:
        raise HTTPException(status_code=400, detail="Stock insuficiente")

    movimiento = MovimientoInventario(
        producto_id=producto.id,
        proveedor_id=None,
        tipo="salida",
        cantidad=datos.cantidad,
        motivo=motivo_norm,
    )
    db.add(movimiento)
    db.commit()
    db.refresh(movimiento)
    return movimiento


def calcular_stock(db: Session, codigo: str) -> dict:
    """Calcula stock actual para un producto (RF-4 helper para tests)."""
    codigo_norm = codigo.strip().upper()
    producto = db.query(Producto).filter(Producto.sku == codigo_norm).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    calc = _calcular_stock_actual(db, producto.id, producto.stock_inicial)
    return {
        "codigo": producto.sku,
        "nombre": producto.nombre,
        "stock_inicial": producto.stock_inicial,
        **calc,
    }


def listar_historial(
    db: Session, producto_codigo: str | None = None, tipo: str | None = None
) -> list[MovimientoInventario]:
    """Lista historial ordenado por fecha DESC, id DESC, con filtros opcionales (RF-3)."""
    query = db.query(MovimientoInventario)

    if producto_codigo is not None:
        codigo_norm = producto_codigo.strip().upper()
        producto = db.query(Producto).filter(Producto.sku == codigo_norm).first()
        if producto is None:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        query = query.filter(MovimientoInventario.producto_id == producto.id)

    if tipo is not None:
        if tipo not in ("entrada", "salida", "entrada_inicial"):
            raise HTTPException(status_code=422, detail="Tipo inválido")
        query = query.filter(MovimientoInventario.tipo == tipo)

    return query.order_by(
        MovimientoInventario.created_at.desc(), MovimientoInventario.id.desc()
    ).all()


def listar_stock(db: Session, incluir_inactivos: bool = False) -> list[dict]:
    """Lista stock actual global, solo activos por defecto (RF-4)."""
    query = db.query(Producto)
    if not incluir_inactivos:
        query = query.filter(Producto.estado == "activo")
    productos = query.order_by(Producto.sku).all()
    result: list[dict] = []
    for prod in productos:
        calc = _calcular_stock_actual(db, prod.id, prod.stock_inicial)
        result.append(
            {
                "codigo": prod.sku,
                "nombre": prod.nombre,
                "stock_inicial": prod.stock_inicial,
                **calc,
            }
        )
    return result
