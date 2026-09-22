"""Service de ventas — validación 422→404→400 y orquestación (RF-1, RF-2)."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import TYPE_CHECKING

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.movimiento_inventario import MovimientoInventario
from app.models.producto import Producto
from app.services.auth_service import validar_email_formato

if TYPE_CHECKING:
    from app.models.venta import Venta

_PRODUCTO_REGEX = re.compile(r"^[A-Z0-9_-]{3,20}$")


def _validar_cliente(cliente: dict | None) -> None:
    """Valida cliente sin BD: nombre 2-100, email ''→422 null/ausente→ok."""
    if cliente is None or not isinstance(cliente, dict):
        raise HTTPException(status_code=422, detail="Cliente requerido")
    nombre = cliente.get("nombre")
    if (
        not isinstance(nombre, str)
        or len(nombre.strip()) < 2
        or len(nombre.strip()) > 100
    ):
        raise HTTPException(
            status_code=422, detail="Nombre debe tener entre 2 y 100 caracteres"
        )
    email = cliente.get("email")
    if email is None:
        return
    if not isinstance(email, str):
        raise HTTPException(status_code=422, detail="Email debe ser texto")
    if email.strip() == "":
        raise HTTPException(status_code=422, detail="Email no puede ser vacío")
    # validar formato si se informa (no null)
    if not validar_email_formato(email):
        raise HTTPException(status_code=422, detail="Email formato inválido")


def _validar_item_formato(item: dict) -> str:
    """Valida un ítem sin BD y retorna código normalizado."""
    codigo_raw = item.get("producto_codigo")
    if not isinstance(codigo_raw, str):
        raise HTTPException(status_code=422, detail="producto_codigo debe ser texto")
    codigo_norm = codigo_raw.strip().upper()
    if not _PRODUCTO_REGEX.fullmatch(codigo_norm):
        raise HTTPException(
            status_code=422,
            detail="producto_codigo debe tener 3-20 caracteres alfanuméricos, _ o -",
        )

    cantidad = item.get("cantidad")
    # cantidad debe ser entero en JSON, rechaza decimal con parte fraccional y string
    if isinstance(cantidad, bool):
        raise HTTPException(status_code=422, detail="cantidad debe ser entero")
    if not isinstance(cantidad, int):
        raise HTTPException(status_code=422, detail="cantidad debe ser entero")
    if cantidad < 1 or cantidad > 1000000:
        raise HTTPException(
            status_code=422, detail="cantidad debe estar entre 1 y 1000000"
        )

    precio_raw = item.get("precio_unitario")
    # precio debe ser Decimal, no float ni string (estricto para service directo)
    if isinstance(precio_raw, float):
        raise HTTPException(
            status_code=422, detail="precio_unitario debe ser Decimal, no float"
        )
    if isinstance(precio_raw, str):
        raise HTTPException(
            status_code=422, detail="precio_unitario debe ser Decimal, no string"
        )
    if not isinstance(precio_raw, Decimal):
        raise HTTPException(status_code=422, detail="precio_unitario debe ser Decimal")
    if precio_raw.as_tuple().exponent < -2:  # type: ignore[operator]
        raise HTTPException(
            status_code=422, detail="precio_unitario debe tener máximo 2 decimales"
        )
    if precio_raw < Decimal(0) or precio_raw > Decimal(1000000):
        raise HTTPException(
            status_code=422, detail="precio_unitario debe estar entre 0 y 1000000"
        )

    return codigo_norm


def validar_formato(items: list[dict], cliente: dict | None) -> None:
    """Valida formato/estructura sin BD: carrito 1-20, duplicado, producto_codigo, cantidad, precio, cliente. 422 si falla."""
    # cliente
    _validar_cliente(cliente)

    # items tamaño
    if not isinstance(items, list) or len(items) < 1 or len(items) > 20:
        raise HTTPException(
            status_code=422, detail="items debe tener entre 1 y 20 elementos"
        )

    codigos_norm: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            raise HTTPException(status_code=422, detail="item debe ser objeto")
        codigo_norm = _validar_item_formato(item)
        codigos_norm.append(codigo_norm)

    if len(codigos_norm) != len(set(codigos_norm)):
        raise HTTPException(
            status_code=422, detail="SKU duplicado en el carrito tras normalización"
        )


def validar_existencia_y_activo(db: Session, items: list[dict]) -> None:
    """Valida contra BD: existencia 404 y estado activo 400 para cada producto_codigo."""
    for item in items:
        codigo_raw = item.get("producto_codigo", "")
        codigo_norm = str(codigo_raw).strip().upper()
        producto = db.query(Producto).filter(Producto.sku == codigo_norm).first()
        if producto is None:
            raise HTTPException(
                status_code=404, detail=f"Producto no encontrado: {codigo_norm}"
            )
        if producto.estado != "activo":
            raise HTTPException(
                status_code=400, detail=f"Producto inactivo: {codigo_norm}"
            )


def registrar_venta(db: Session, datos: dict) -> "Venta":
    """Registra venta y N salidas en una sola transacción atómica (RF-2, RNF-2).

    Orden: validar_formato (422) → validar_existencia_y_activo (404/400) →
    validar_stock_suficiente (400 con detalle) → calcular_totales (Decimal) →
    crear venta + N movimientos salida + N venta_items con movimiento_id,
    todo en un único BEGIN/COMMIT. Si cualquier ítem falla, rollback total.
    Reutiliza MovimientoInventario directamente (no llama a registrar_salida
    con commit separado) pero respeta su lógica de stock (SELECT FOR UPDATE).
    """
    from app.models.movimiento_inventario import MovimientoInventario
    from app.models.venta import Venta
    from app.models.venta_item import VentaItem

    cliente = datos.get("cliente")
    items = datos.get("items")

    # 1) Validación sin BD ya pasó en schemas, pero revalidamos por seguridad (422)
    validar_formato(items, cliente)  # type: ignore[arg-type]

    # 2) Validación con BD: existencia y activo (404/400) — antes de stock
    validar_existencia_y_activo(db, items)  # type: ignore[arg-type]
    # 3) Validación de stock con SELECT FOR UPDATE y mensaje específico (400)
    validar_stock_suficiente(db, items)  # type: ignore[arg-type]

    # 4) Cálculo Decimal exacto
    subtotales, total = calcular_totales(items)  # type: ignore[arg-type]

    # 5) Transacción atómica: venta + N salidas + N venta_items
    try:
        # Crear venta cabecera
        cliente_nombre = str(cliente.get("nombre", "")).strip()  # type: ignore[union-attr]
        cliente_email_raw = cliente.get("email")  # type: ignore[union-attr]
        cliente_email = None
        if isinstance(cliente_email_raw, str) and cliente_email_raw.strip() != "":
            cliente_email = cliente_email_raw.strip().lower()
        elif cliente_email_raw is None:
            cliente_email = None
        else:
            # Si es string vacío, ya habría sido 422 en validar_formato, pero por seguridad
            cliente_email = None

        venta = Venta(
            cliente_nombre=cliente_nombre,
            cliente_email=cliente_email,
            total=total,
        )
        db.add(venta)
        db.flush()  # para obtener venta.id sin commit

        # Para cada ítem, crear movimiento salida y venta_item
        for idx, item in enumerate(items):  # type: ignore[arg-type]
            codigo_norm = str(item.get("producto_codigo", "")).strip().upper()
            cantidad = int(item.get("cantidad"))  # type: ignore[arg-type]
            precio = item.get("precio_unitario")  # Decimal
            subtotal = subtotales[idx]

            producto = db.query(Producto).filter(Producto.sku == codigo_norm).first()
            # producto ya validado, pero re-obtenemos para id
            assert producto is not None
            # Crear movimiento salida directamente (sin commit separado)
            movimiento = MovimientoInventario(
                producto_id=producto.id,
                proveedor_id=None,
                tipo="salida",
                cantidad=cantidad,
                motivo=f"venta #{venta.id}",
            )
            db.add(movimiento)
            db.flush()  # para obtener movimiento.id

            # Crear venta_item con referencia a movimiento
            producto_id = int(producto.id)  # type: ignore[arg-type]
            venta_item = VentaItem(
                venta_id=venta.id,
                producto_id=producto_id,
                cantidad=cantidad,
                precio_unitario=precio,
                subtotal=subtotal,
                movimiento_id=movimiento.id,
            )
            db.add(venta_item)

        db.commit()
        db.refresh(venta)
        return venta
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al registrar venta") from exc


def calcular_stock_actual(db: Session, producto_codigo: str) -> int:
    """Calcula stock_actual para un producto con SELECT FOR UPDATE (como en 003).

    Lee stock_inicial + SUM(entrada) - SUM(salida). Usa SELECT FOR UPDATE para serializar.
    """
    codigo_norm = producto_codigo.strip().upper()
    producto = db.query(Producto).filter(Producto.sku == codigo_norm).first()
    if producto is None:
        raise HTTPException(
            status_code=404, detail=f"Producto no encontrado: {codigo_norm}"
        )
    # Bloqueo pesimista para serializar (en SQLite se ignora si no soporta)
    try:
        db.query(Producto).filter(Producto.id == producto.id).with_for_update().first()  # type: ignore[attr-defined]
    except Exception:
        pass
    entradas = (
        db.query(func.coalesce(func.sum(MovimientoInventario.cantidad), 0))
        .filter(
            MovimientoInventario.producto_id == producto.id,
            MovimientoInventario.tipo == "entrada",
        )
        .scalar()
    )
    salidas = (
        db.query(func.coalesce(func.sum(MovimientoInventario.cantidad), 0))
        .filter(
            MovimientoInventario.producto_id == producto.id,
            MovimientoInventario.tipo == "salida",
        )
        .scalar()
    )
    stock_actual = int(producto.stock_inicial) + int(entradas or 0) - int(salidas or 0)
    return stock_actual


def validar_stock_suficiente(db: Session, items: list[dict]) -> None:
    """Valida que cada ítem tenga stock suficiente, con mensaje específico por producto. 400 si falla."""
    for item in items:
        codigo_raw = item.get("producto_codigo", "")
        codigo_norm = str(codigo_raw).strip().upper()
        cantidad = item.get("cantidad")
        # cantidad ya validada como int en validar_formato, pero revalidamos tipo
        if not isinstance(cantidad, int) or isinstance(cantidad, bool):
            raise HTTPException(status_code=422, detail="cantidad debe ser entero")
        stock_actual = calcular_stock_actual(db, codigo_norm)
        if cantidad > stock_actual:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para el producto {codigo_norm}: disponible {stock_actual}, solicitado {cantidad}",
            )


def calcular_totales(items: list[dict]) -> tuple[list[Decimal], Decimal]:
    """Calcula subtotales y total con Decimal exacto, nunca float."""
    subtotales: list[Decimal] = []
    total = Decimal("0.00")
    for item in items:
        cantidad = item.get("cantidad")
        precio_raw = item.get("precio_unitario")
        # Asegurar que son Decimal e int ya validados
        if not isinstance(cantidad, int) or isinstance(cantidad, bool):
            raise HTTPException(status_code=422, detail="cantidad debe ser entero")
        if not isinstance(precio_raw, Decimal):
            raise HTTPException(
                status_code=422, detail="precio_unitario debe ser Decimal"
            )
        subtotal = Decimal(cantidad) * precio_raw
        # Normalizar a 2 decimales
        subtotal = subtotal.quantize(Decimal("0.00"))
        subtotales.append(subtotal)
        total += subtotal
    total = total.quantize(Decimal("0.00"))
    return subtotales, total
