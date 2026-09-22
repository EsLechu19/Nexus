"""Tests de T07 004 — Unitarios de service stock (mock + sqlite) RF-1."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.schemas.movimiento import MovimientoCreateEntrada, MovimientoCreateSalida
from app.schemas.producto import ProductoCreate
from app.schemas.proveedor import ProveedorCreate


def _make_session():
    from app.models.movimiento_inventario import MovimientoInventario  # noqa: F401
    from app.models.producto import Producto  # noqa: F401
    from app.models.proveedor import Proveedor  # noqa: F401

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


def test_stock_sin_movimientos_igual_a_inicial():
    from app.services.stock_service import calcular_stock

    SessionLocal = _make_session()
    db = SessionLocal()
    _crear_producto(db, codigo="PROD-001", stock_inicial=5, stock_minimo=10)
    stock = calcular_stock(db, "PROD-001")
    assert stock["stock_actual"] == 5
    db.close()


def test_stock_minimo_cero_nunca_alerta():
    from app.services.stock_service import calcular_stock

    SessionLocal = _make_session()
    db = SessionLocal()
    _crear_producto(db, codigo="PROD-002", stock_inicial=0, stock_minimo=0)
    stock = calcular_stock(db, "PROD-002")
    assert stock["alerta"] is False
    assert stock["stock_actual"] == 0
    # Con stock 5 y minimo 0 también false
    _crear_producto(db, codigo="PROD-003", stock_inicial=5, stock_minimo=0)
    assert calcular_stock(db, "PROD-003")["alerta"] is False
    db.close()


def test_stock_igual_minimo_false():
    from app.services.stock_service import calcular_stock

    SessionLocal = _make_session()
    db = SessionLocal()
    _crear_producto(db, codigo="PROD-004", stock_inicial=5, stock_minimo=5)
    stock = calcular_stock(db, "PROD-004")
    assert stock["alerta"] is False  # 5==5
    db.close()


def test_stock_cero_con_minimo_true():
    from app.services.stock_service import calcular_stock

    SessionLocal = _make_session()
    db = SessionLocal()
    _crear_producto(db, codigo="PROD-005", stock_inicial=0, stock_minimo=5)
    stock = calcular_stock(db, "PROD-005")
    assert stock["alerta"] is True
    db.close()


def test_stock_5_mas_10_menos_3_igual_12():
    from app.services.movimiento_service import registrar_entrada, registrar_salida
    from app.services.stock_service import calcular_stock

    SessionLocal = _make_session()
    db = SessionLocal()
    _crear_producto(db, codigo="PROD-006", stock_inicial=5, stock_minimo=10)
    _crear_proveedor(db, codigo="PROV-001")
    registrar_entrada(
        db,
        MovimientoCreateEntrada(
            producto_codigo="PROD-006", proveedor_codigo="PROV-001", cantidad=10
        ),
    )
    registrar_salida(db, MovimientoCreateSalida(producto_codigo="PROD-006", cantidad=3))
    stock = calcular_stock(db, "PROD-006")
    assert stock["stock_actual"] == 12
    assert stock["alerta"] is False  # 12 >=10
    # Salida 5 deja 7 <10 -> true
    registrar_salida(db, MovimientoCreateSalida(producto_codigo="PROD-006", cantidad=5))
    stock = calcular_stock(db, "PROD-006")
    assert stock["stock_actual"] == 7
    assert stock["alerta"] is True
    db.close()


def test_stock_codigo_normalizado_y_inactivo_404():
    from fastapi import HTTPException

    from app.services.stock_service import calcular_stock

    SessionLocal = _make_session()
    db = SessionLocal()
    _crear_producto(db, codigo="PROD-007", stock_inicial=5, stock_minimo=10)
    stock = calcular_stock(db, "  prod-007 ")
    assert stock["codigo"] == "PROD-007"
    with pytest.raises(HTTPException) as exc:
        calcular_stock(db, "NOPE")
    assert exc.value.status_code == 404
    from app.models.producto import Producto

    prod = db.query(Producto).filter(Producto.sku == "PROD-007").first()
    prod.estado = "inactivo"
    db.commit()
    with pytest.raises(HTTPException) as exc:
        calcular_stock(db, "PROD-007")
    assert exc.value.status_code == 404
    db.close()


def test_stock_minimo_null_ausente_vacio():
    """ProductoCreate stock_minimo null/ausente ->0, '' ->422, -5/>1M ->422."""
    from pydantic import ValidationError

    from app.schemas.producto import ProductoCreate

    obj = ProductoCreate(
        sku="SKU-001", nombre="Test", categoria="videojuego", stock_minimo=None
    )  # type: ignore
    assert obj.stock_minimo == 0
    obj2 = ProductoCreate(sku="SKU-002", nombre="Test", categoria="videojuego")
    assert obj2.stock_minimo == 0
    for invalido in ["", -5, 1000001, "10"]:
        with pytest.raises(ValidationError):
            ProductoCreate(
                sku="SKU-003",
                nombre="Test",
                categoria="videojuego",
                stock_minimo=invalido,
            )  # type: ignore
