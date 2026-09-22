"""Tests de T03 004 — Service stock_service cálculo y alerta (RF-1)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.schemas.producto import ProductoCreate
from app.schemas.proveedor import ProveedorCreate
from app.schemas.movimiento import MovimientoCreateEntrada, MovimientoCreateSalida


def _make_session():
    from app.models.producto import Producto  # noqa: F401
    from app.models.proveedor import Proveedor  # noqa: F401
    from app.models.movimiento_inventario import MovimientoInventario  # noqa: F401

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def _crear_producto(db, codigo="PROD-001", stock_inicial=5, stock_minimo=0):
    from app.services.producto_service import crear_producto

    return crear_producto(
        db,
        ProductoCreate(
            sku=codigo,
            nombre="Producto Test",
            categoria="videojuego",
            stock_inicial=stock_inicial,
            stock_minimo=stock_minimo,
        ),
    )


def _crear_proveedor(db, codigo="PROV-001"):
    from app.services.proveedor_service import crear_proveedor

    return crear_proveedor(db, ProveedorCreate(codigo=codigo, nombre="Proveedor Test"))


def test_calcular_stock_sin_movimientos():
    """RF-1: sin movimientos stock_actual == stock_inicial, alerta según mínimo."""
    from app.services.stock_service import calcular_stock

    SessionLocal = _make_session()
    db = SessionLocal()
    _crear_producto(db, codigo="PROD-001", stock_inicial=5, stock_minimo=10)
    stock = calcular_stock(db, "PROD-001")
    assert stock["stock_actual"] == 5
    assert stock["stock_inicial"] == 5
    assert stock["stock_minimo"] == 10
    assert stock["alerta"] is True
    assert stock["entradas"] == 0 and stock["salidas"] == 0
    db.close()


def test_calcular_stock_con_movimientos_y_alerta():
    """RF-1: 5 inicial +10 entradas -3 salidas =12, mínimo 10 -> false, luego 7 -> true."""
    from app.services.stock_service import calcular_stock
    from app.services.movimiento_service import registrar_entrada, registrar_salida

    SessionLocal = _make_session()
    db = SessionLocal()
    _crear_producto(db, codigo="PROD-002", stock_inicial=5, stock_minimo=10)
    _crear_proveedor(db, codigo="PROV-001")
    registrar_entrada(
        db,
        MovimientoCreateEntrada(
            producto_codigo="PROD-002", proveedor_codigo="PROV-001", cantidad=10
        ),
    )
    registrar_salida(db, MovimientoCreateSalida(producto_codigo="PROD-002", cantidad=3))
    stock = calcular_stock(db, "PROD-002")
    assert stock["stock_actual"] == 12
    assert stock["alerta"] is False
    # Salida 5 deja 7 <10 -> true
    registrar_salida(db, MovimientoCreateSalida(producto_codigo="PROD-002", cantidad=5))
    stock = calcular_stock(db, "PROD-002")
    assert stock["stock_actual"] == 7
    assert stock["alerta"] is True
    db.close()


def test_calcular_stock_minimo_cero_nunca_alerta():
    """RF-1: stock_minimo 0 -> alerta false siempre."""
    from app.services.stock_service import calcular_stock

    SessionLocal = _make_session()
    db = SessionLocal()
    _crear_producto(db, codigo="PROD-003", stock_inicial=0, stock_minimo=0)
    stock = calcular_stock(db, "PROD-003")
    assert stock["alerta"] is False
    assert stock["stock_actual"] == 0
    db.close()


def test_calcular_stock_igual_minimo_false():
    """RF-1: stock_actual == stock_minimo -> false (solo < dispara)."""
    from app.services.stock_service import calcular_stock

    SessionLocal = _make_session()
    db = SessionLocal()
    _crear_producto(db, codigo="PROD-004", stock_inicial=5, stock_minimo=5)
    stock = calcular_stock(db, "PROD-004")
    assert stock["alerta"] is False  # 5==5
    # Crear otro con 0/5 -> true
    _crear_producto(db, codigo="PROD-005", stock_inicial=0, stock_minimo=5)
    stock2 = calcular_stock(db, "PROD-005")
    assert stock2["alerta"] is True
    db.close()


def test_calcular_stock_normaliza_codigo_y_404():
    """RF-1: normaliza trim+upper, 404 si no existe o inactivo."""
    from fastapi import HTTPException
    from app.services.stock_service import calcular_stock

    SessionLocal = _make_session()
    db = SessionLocal()
    _crear_producto(db, codigo="PROD-006", stock_inicial=5)
    stock = calcular_stock(db, "  prod-006 ")
    assert stock["codigo"] == "PROD-006"
    with pytest.raises(HTTPException) as exc:
        calcular_stock(db, "NOPE")
    assert exc.value.status_code == 404
    # Inactivo -> 404
    from app.models.producto import Producto

    prod = db.query(Producto).filter(Producto.sku == "PROD-006").first()
    prod.estado = "inactivo"
    db.commit()
    with pytest.raises(HTTPException) as exc:
        calcular_stock(db, "PROD-006")
    assert exc.value.status_code == 404
    db.close()


def test_listar_stock_global_solo_activos_ordenados():
    """RF-1: global solo activos ordenados por codigo, con alerta."""
    from app.services.stock_service import listar_stock

    SessionLocal = _make_session()
    db = SessionLocal()
    _crear_producto(db, codigo="PROD-010", stock_inicial=1, stock_minimo=5)
    _crear_producto(db, codigo="PROD-002", stock_inicial=2, stock_minimo=0)
    prod_inactivo = _crear_producto(db, codigo="PROD-003", stock_inicial=3)
    prod_inactivo.estado = "inactivo"
    db.commit()
    stocks = listar_stock(db)
    assert [s["codigo"] for s in stocks] == ["PROD-002", "PROD-010"]
    for s in stocks:
        assert "alerta" in s and "stock_minimo" in s
    # Con incluir_inactivos
    stocks_all = listar_stock(db, incluir_inactivos=True)
    assert len(stocks_all) == 3
    db.close()


def test_listar_stock_vacio():
    """RF-1: sin productos activos -> []"""
    from app.services.stock_service import listar_stock

    SessionLocal = _make_session()
    db = SessionLocal()
    assert listar_stock(db) == []
    db.close()
