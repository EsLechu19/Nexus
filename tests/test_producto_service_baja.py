"""Tests de T08 — Service baja_producto (RF-5)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.schemas.producto import ProductoCreate


def _make_session():
    from app.models.movimiento_inventario import MovimientoInventario  # noqa: F401
    from app.models.producto import Producto  # noqa: F401

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _crear(
    db, sku="BAJA-001", nombre="Producto Baja", categoria="videojuego", stock_inicial=0
):
    from app.services.producto_service import crear_producto

    return crear_producto(
        db,
        ProductoCreate(
            sku=sku, nombre=nombre, categoria=categoria, stock_inicial=stock_inicial
        ),
    )


def test_baja_producto_activo_a_inactivo():
    """RF-5: marca activo -> inactivo."""
    from app.services.producto_service import baja_producto

    db = _make_session()
    _crear(db, sku="BAJA-001")
    prod = baja_producto(db, "BAJA-001")
    assert prod.estado == "inactivo"
    assert prod.sku == "BAJA-001"
    db.close()


def test_baja_producto_con_stock_inicial_mayor_cero_permite():
    """RF-5: permite baja con cualquier stock_inicial."""
    from app.services.producto_service import baja_producto

    db = _make_session()
    _crear(db, sku="BAJA-002", stock_inicial=50)
    prod = baja_producto(db, "BAJA-002")
    assert prod.estado == "inactivo"
    assert prod.stock_inicial == 50
    db.close()


def test_baja_producto_ya_inactivo_400():
    """RF-5: ya inactivo -> 400, no idempotente."""
    from fastapi import HTTPException

    from app.services.producto_service import baja_producto

    db = _make_session()
    _crear(db, sku="BAJA-003")
    baja_producto(db, "BAJA-003")
    with pytest.raises(HTTPException) as exc:
        baja_producto(db, "BAJA-003")
    assert exc.value.status_code == 400
    assert "ya" in exc.value.detail.lower() or "inactivo" in exc.value.detail.lower()
    db.close()


def test_baja_producto_no_encontrado_404():
    """RF-5: SKU inexistente -> 404."""
    from fastapi import HTTPException

    from app.services.producto_service import baja_producto

    db = _make_session()
    with pytest.raises(HTTPException) as exc:
        baja_producto(db, "NO-EXISTE")
    assert exc.value.status_code == 404
    db.close()


def test_baja_producto_normaliza_sku_path():
    """RF-5: SKU path normalizado trim+upper."""
    from app.services.producto_service import baja_producto

    db = _make_session()
    _crear(db, sku="BAJA-004")
    prod = baja_producto(db, "  baja-004 ")
    assert prod.estado == "inactivo"
    db.close()


def test_baja_producto_no_borra_fisicamente_y_excluido_de_listado():
    """RF-5 y RNF-1: no borra, excluido de listar_activos pero visible en obtener_por_sku."""
    from app.models.producto import Producto
    from app.services.producto_service import (
        baja_producto,
        listar_activos,
        obtener_por_sku,
    )

    db = _make_session()
    _crear(db, sku="BAJA-005", nombre="Visible", categoria="consola")
    _crear(db, sku="BAJA-006", nombre="Otro", categoria="videojuego")
    baja_producto(db, "BAJA-005")

    # sigue en DB
    assert db.query(Producto).filter(Producto.sku == "BAJA-005").first() is not None
    # excluido de activos
    activos = listar_activos(db)
    assert {p.sku for p in activos} == {"BAJA-006"}
    # visible via detalle
    prod = obtener_por_sku(db, "BAJA-005")
    assert prod.estado == "inactivo"
    db.close()


def test_baja_producto_no_borra_movimiento_inicial():
    """RNF-1: traza inicial permanece tras baja."""
    from app.models.movimiento_inventario import MovimientoInventario
    from app.services.producto_service import baja_producto

    db = _make_session()
    _crear(db, sku="BAJA-007", stock_inicial=10)
    assert db.query(MovimientoInventario).count() == 1
    baja_producto(db, "BAJA-007")
    assert db.query(MovimientoInventario).count() == 1
    db.close()
