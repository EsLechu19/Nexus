"""Tests de T03 — Service registrar_entrada (RF-1)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.schemas.movimiento import MovimientoCreateEntrada
from app.schemas.producto import ProductoCreate
from app.schemas.proveedor import ProveedorCreate


def _make_session():
    from app.models.movimiento_inventario import MovimientoInventario  # noqa: F401
    from app.models.producto import Producto  # noqa: F401
    from app.models.proveedor import Proveedor  # noqa: F401

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _crear_producto(db, codigo="PROD-001", stock_inicial=5):
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


def test_registrar_entrada_valida_incrementa_stock():
    """RF-1: entrada válida incrementa stock y retorna movimiento."""
    from app.services.movimiento_service import calcular_stock, registrar_entrada

    db = _make_session()
    _crear_producto(db, codigo="PROD-001", stock_inicial=5)
    _crear_proveedor(db, codigo="PROV-001")
    mov = registrar_entrada(
        db,
        MovimientoCreateEntrada(
            producto_codigo="PROD-001",
            proveedor_codigo="PROV-001",
            cantidad=10,
            motivo="Compra",
        ),
    )
    assert mov.tipo == "entrada"
    assert mov.cantidad == 10
    assert mov.proveedor_id is not None
    stock = calcular_stock(db, "PROD-001")
    assert stock["stock_actual"] == 15  # 5 inicial +10 entrada
    assert stock["entradas"] == 10
    db.close()


def test_registrar_entrada_sin_motivo():
    """RF-1: motivo null/ausente -> None."""
    from app.services.movimiento_service import registrar_entrada

    db = _make_session()
    _crear_producto(db, codigo="PROD-002")
    _crear_proveedor(db, codigo="PROV-002")
    mov = registrar_entrada(
        db,
        MovimientoCreateEntrada(
            producto_codigo="PROD-002", proveedor_codigo="PROV-002", cantidad=5
        ),
    )
    assert mov.motivo is None
    db.close()


def test_registrar_entrada_normaliza_codigos():
    """RF-1: códigos trim+upper."""
    from app.services.movimiento_service import registrar_entrada

    db = _make_session()
    _crear_producto(db, codigo="PROD-003")
    _crear_proveedor(db, codigo="PROV-003")
    mov = registrar_entrada(
        db,
        MovimientoCreateEntrada(
            producto_codigo="  prod-003 ", proveedor_codigo="  prov-003 ", cantidad=1
        ),
    )
    assert mov.cantidad == 1
    db.close()


def test_registrar_entrada_producto_no_existe_404():
    """RF-1: producto no existe -> 404."""
    from fastapi import HTTPException

    from app.services.movimiento_service import registrar_entrada

    db = _make_session()
    _crear_proveedor(db, codigo="PROV-004")
    with pytest.raises(HTTPException) as exc:
        registrar_entrada(
            db,
            MovimientoCreateEntrada(
                producto_codigo="NOPE", proveedor_codigo="PROV-004", cantidad=1
            ),
        )
    assert exc.value.status_code == 404
    db.close()


def test_registrar_entrada_producto_inactivo_400():
    """RF-1: producto inactivo -> 400."""
    from fastapi import HTTPException

    from app.services.movimiento_service import registrar_entrada

    db = _make_session()
    prod = _crear_producto(db, codigo="PROD-005")
    _crear_proveedor(db, codigo="PROV-005")
    prod.estado = "inactivo"
    db.commit()
    with pytest.raises(HTTPException) as exc:
        registrar_entrada(
            db,
            MovimientoCreateEntrada(
                producto_codigo="PROD-005", proveedor_codigo="PROV-005", cantidad=1
            ),
        )
    assert exc.value.status_code == 400
    db.close()


def test_registrar_entrada_proveedor_no_existe_404():
    """RF-1: proveedor no existe -> 404."""
    from fastapi import HTTPException

    from app.services.movimiento_service import registrar_entrada

    db = _make_session()
    _crear_producto(db, codigo="PROD-006")
    with pytest.raises(HTTPException) as exc:
        registrar_entrada(
            db,
            MovimientoCreateEntrada(
                producto_codigo="PROD-006", proveedor_codigo="NOPE", cantidad=1
            ),
        )
    assert exc.value.status_code == 404
    db.close()


def test_registrar_entrada_proveedor_inactivo_400():
    """RF-1: proveedor inactivo -> 400."""
    from fastapi import HTTPException

    from app.services.movimiento_service import registrar_entrada

    db = _make_session()
    _crear_producto(db, codigo="PROD-007")
    prov = _crear_proveedor(db, codigo="PROV-007")
    prov.estado = "inactivo"
    db.commit()
    with pytest.raises(HTTPException) as exc:
        registrar_entrada(
            db,
            MovimientoCreateEntrada(
                producto_codigo="PROD-007", proveedor_codigo="PROV-007", cantidad=1
            ),
        )
    assert exc.value.status_code == 400
    db.close()


def test_registrar_entrada_cantidad_invalida_422_schema():
    """RF-1: cantidad 0/negativa/decimal/>1M ya validada en schema -> 422, pero service no la recibe."""
    from pydantic import ValidationError

    from app.schemas.movimiento import MovimientoCreateEntrada

    for invalido in [0, -1, 1000001, 1.5, "10"]:
        with pytest.raises(ValidationError):
            MovimientoCreateEntrada(
                producto_codigo="PROD-001",
                proveedor_codigo="PROV-001",
                cantidad=invalido,
            )  # type: ignore


def test_registrar_entrada_motivo_invalido_422_schema():
    """RF-1: motivo ''/1/201/\\n -> 422 en schema."""
    from pydantic import ValidationError

    from app.schemas.movimiento import MovimientoCreateEntrada

    for invalido in ["", "A", "A" * 201, "a\nb"]:
        with pytest.raises(ValidationError):
            MovimientoCreateEntrada(
                producto_codigo="PROD-001",
                proveedor_codigo="PROV-001",
                cantidad=1,
                motivo=invalido,
            )
