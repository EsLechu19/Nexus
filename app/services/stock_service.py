"""Service de consulta de stock — reutiliza cálculo de movimientos (RF-1)."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.producto import Producto
from app.services.movimiento_service import _calcular_stock_actual


def calcular_stock(db: Session, codigo: str) -> dict:
    """Calcula stock actual y alerta para un producto activo (RF-1)."""
    codigo_norm = codigo.strip().upper()
    producto = db.query(Producto).filter(Producto.sku == codigo_norm).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if producto.estado != "activo":
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    calc = _calcular_stock_actual(db, producto.id, producto.stock_inicial)
    stock_minimo = producto.stock_minimo if producto.stock_minimo is not None else 0
    alerta = stock_minimo > 0 and calc["stock_actual"] < stock_minimo
    return {
        "codigo": producto.sku,
        "nombre": producto.nombre,
        "stock_inicial": producto.stock_inicial,
        "stock_minimo": stock_minimo,
        "entradas": calc["entradas"],
        "salidas": calc["salidas"],
        "stock_actual": calc["stock_actual"],
        "alerta": alerta,
    }


def listar_stock(db: Session, incluir_inactivos: bool = False) -> list[dict]:
    """Lista stock global, solo activos por defecto ordenados por codigo (RF-1)."""
    query = db.query(Producto)
    if not incluir_inactivos:
        query = query.filter(Producto.estado == "activo")
    productos = query.order_by(Producto.sku).all()
    result: list[dict] = []
    for prod in productos:
        calc = _calcular_stock_actual(db, prod.id, prod.stock_inicial)
        stock_minimo = prod.stock_minimo if prod.stock_minimo is not None else 0
        alerta = stock_minimo > 0 and calc["stock_actual"] < stock_minimo
        result.append(
            {
                "codigo": prod.sku,
                "nombre": prod.nombre,
                "stock_inicial": prod.stock_inicial,
                "stock_minimo": stock_minimo,
                "entradas": calc["entradas"],
                "salidas": calc["salidas"],
                "stock_actual": calc["stock_actual"],
                "alerta": alerta,
            }
        )
    return result
