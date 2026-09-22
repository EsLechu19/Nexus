"""Tests de T04 — Service registrar_salida (RF-2)."""

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
    return sessionmaker(bind=engine)()


def _crear_producto(db, codigo="PROD-001", stock_inicial=10):
    from app.services.producto_service import crear_producto

    return crear_producto(
        db,
        ProductoCreate(
            sku=codigo,
            nombre="Producto Test",
            categoria="videojuego",
            stock_inicial=stock_inicial,
        ),
    )


def _crear_proveedor(db, codigo="PROV-001"):
    from app.services.proveedor_service import crear_proveedor

    return crear_proveedor(db, ProveedorCreate(codigo=codigo, nombre="Proveedor Test"))


def test_registrar_salida_valida_decrementa_stock():
    """RF-2: salida válida decrementa stock."""
    from app.services.movimiento_service import (
        calcular_stock,
        registrar_entrada,
        registrar_salida,
    )

    db = _make_session()
    _crear_producto(db, codigo="PROD-001", stock_inicial=10)
    _crear_proveedor(db, codigo="PROV-001")
    registrar_entrada(
        db,
        MovimientoCreateEntrada(
            producto_codigo="PROD-001", proveedor_codigo="PROV-001", cantidad=5
        ),
    )
    mov = registrar_salida(
        db,
        MovimientoCreateSalida(producto_codigo="PROD-001", cantidad=8, motivo="Venta"),
    )
    assert mov.tipo == "salida"
    assert mov.proveedor_id is None
    stock = calcular_stock(db, "PROD-001")
    assert stock["stock_actual"] == 7  # 10 inicial +5 -8 =7
    assert stock["entradas"] == 5 and stock["salidas"] == 8
    db.close()


def test_registrar_salida_exacta_deja_cero():
    """RF-2: salida exacta deja 0."""
    from app.services.movimiento_service import calcular_stock, registrar_salida

    db = _make_session()
    _crear_producto(db, codigo="PROD-002", stock_inicial=5)
    mov = registrar_salida(
        db, MovimientoCreateSalida(producto_codigo="PROD-002", cantidad=5)
    )
    assert mov.cantidad == 5
    assert calcular_stock(db, "PROD-002")["stock_actual"] == 0
    db.close()


def test_registrar_salida_stock_insuficiente_400():
    """RF-2: stock insuficiente -> 400 sin movimiento."""
    from fastapi import HTTPException

    from app.services.movimiento_service import registrar_salida

    db = _make_session()
    _crear_producto(db, codigo="PROD-003", stock_inicial=5)
    with pytest.raises(HTTPException) as exc:
        registrar_salida(
            db, MovimientoCreateSalida(producto_codigo="PROD-003", cantidad=6)
        )
    assert exc.value.status_code == 400
    assert "stock" in exc.value.detail.lower()
    # Verificar que no se creó movimiento
    from app.models.movimiento_inventario import MovimientoInventario

    assert (
        db.query(MovimientoInventario)
        .filter(MovimientoInventario.tipo == "salida")
        .count()
        == 0
    )
    db.close()


def test_registrar_salida_producto_no_existe_404():
    from fastapi import HTTPException

    from app.services.movimiento_service import registrar_salida

    db = _make_session()
    with pytest.raises(HTTPException) as exc:
        registrar_salida(db, MovimientoCreateSalida(producto_codigo="NOPE", cantidad=1))
    assert exc.value.status_code == 404
    db.close()


def test_registrar_salida_producto_inactivo_400():
    from fastapi import HTTPException

    from app.services.movimiento_service import registrar_salida

    db = _make_session()
    prod = _crear_producto(db, codigo="PROD-004")
    prod.estado = "inactivo"
    db.commit()
    with pytest.raises(HTTPException) as exc:
        registrar_salida(
            db, MovimientoCreateSalida(producto_codigo="PROD-004", cantidad=1)
        )
    assert exc.value.status_code == 400
    db.close()


def test_registrar_salida_proveedor_enviado_422_schema():
    """RF-2: salida no permite proveedor -> 422 en schema."""
    from pydantic import ValidationError

    from app.schemas.movimiento import MovimientoCreateSalida

    with pytest.raises(ValidationError):
        MovimientoCreateSalida(
            producto_codigo="PROD-001", cantidad=1, proveedor_codigo="PROV-001"
        )  # type: ignore


def test_registrar_salida_cantidad_invalida_422_schema():
    from pydantic import ValidationError

    from app.schemas.movimiento import MovimientoCreateSalida

    for invalido in [0, -1, 1000001, 1.5, "10"]:
        with pytest.raises(ValidationError):
            MovimientoCreateSalida(producto_codigo="PROD-001", cantidad=invalido)  # type: ignore


def test_registrar_salida_motivo_invalido_422_schema():
    from pydantic import ValidationError

    from app.schemas.movimiento import MovimientoCreateSalida

    for invalido in ["", "A", "A" * 201, "a\nb"]:
        with pytest.raises(ValidationError):
            MovimientoCreateSalida(
                producto_codigo="PROD-001", cantidad=1, motivo=invalido
            )


def test_registrar_salida_normaliza_codigo():
    from app.services.movimiento_service import registrar_salida

    db = _make_session()
    _crear_producto(db, codigo="PROD-005", stock_inicial=10)
    mov = registrar_salida(
        db, MovimientoCreateSalida(producto_codigo="  prod-005 ", cantidad=1)
    )
    assert mov.cantidad == 1
    db.close()
