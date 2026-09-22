"""Tests de T02 003 — Schemas Movimiento (RF-1, RF-2, RF-3, RF-4)."""

import pytest
from pydantic import ValidationError


def test_movimiento_create_entrada_valido():
    from app.schemas.movimiento import MovimientoCreateEntrada

    obj = MovimientoCreateEntrada(
        producto_codigo="  prod-001 ",
        proveedor_codigo=" prov-002 ",
        cantidad=10,
        motivo="Compra semanal",
    )
    assert obj.producto_codigo == "PROD-001"
    assert obj.proveedor_codigo == "PROV-002"
    assert obj.cantidad == 10
    assert obj.motivo == "Compra semanal"


def test_movimiento_create_entrada_sin_motivo():
    from app.schemas.movimiento import MovimientoCreateEntrada

    obj = MovimientoCreateEntrada(
        producto_codigo="PROD-001", proveedor_codigo="PROV-001", cantidad=5
    )
    assert obj.motivo is None
    obj2 = MovimientoCreateEntrada(
        producto_codigo="PROD-001", proveedor_codigo="PROV-001", cantidad=5, motivo=None
    )  # type: ignore
    assert obj2.motivo is None


def test_movimiento_create_entrada_codigo_normalizacion_y_regex():
    from app.schemas.movimiento import MovimientoCreateEntrada

    with pytest.raises(ValidationError):
        MovimientoCreateEntrada(
            producto_codigo="AB", proveedor_codigo="PROV-001", cantidad=1
        )
    with pytest.raises(ValidationError):
        MovimientoCreateEntrada(
            producto_codigo="PROD-001", proveedor_codigo="AB", cantidad=1
        )
    with pytest.raises(ValidationError):
        MovimientoCreateEntrada(
            producto_codigo="AB 01", proveedor_codigo="PROV-001", cantidad=1
        )


def test_movimiento_create_entrada_cantidad_rango():
    from app.schemas.movimiento import MovimientoCreateEntrada

    for invalido in [0, -1, 1000001, 1.5, "10"]:
        with pytest.raises(ValidationError):
            MovimientoCreateEntrada(
                producto_codigo="PROD-001",
                proveedor_codigo="PROV-001",
                cantidad=invalido,
            )  # type: ignore


def test_movimiento_create_entrada_motivo_validacion():
    from app.schemas.movimiento import MovimientoCreateEntrada

    with pytest.raises(ValidationError):
        MovimientoCreateEntrada(
            producto_codigo="PROD-001",
            proveedor_codigo="PROV-001",
            cantidad=1,
            motivo="",
        )
    with pytest.raises(ValidationError):
        MovimientoCreateEntrada(
            producto_codigo="PROD-001",
            proveedor_codigo="PROV-001",
            cantidad=1,
            motivo="A",
        )
    with pytest.raises(ValidationError):
        MovimientoCreateEntrada(
            producto_codigo="PROD-001",
            proveedor_codigo="PROV-001",
            cantidad=1,
            motivo="A" * 201,
        )
    with pytest.raises(ValidationError):
        MovimientoCreateEntrada(
            producto_codigo="PROD-001",
            proveedor_codigo="PROV-001",
            cantidad=1,
            motivo="a\nb",
        )
    obj = MovimientoCreateEntrada(
        producto_codigo="PROD-001",
        proveedor_codigo="PROV-001",
        cantidad=1,
        motivo="  Motivo con trim  ",
    )
    assert obj.motivo == "Motivo con trim"


def test_movimiento_create_salida_valido_sin_proveedor():
    from app.schemas.movimiento import MovimientoCreateSalida

    obj = MovimientoCreateSalida(producto_codigo="PROD-001", cantidad=5, motivo="Venta")
    assert obj.producto_codigo == "PROD-001"
    assert obj.cantidad == 5
    assert (
        not hasattr(obj, "proveedor_codigo")
        or getattr(obj, "proveedor_codigo", None) is None
    )


def test_movimiento_create_salida_proveedor_prohibido_422():
    from app.schemas.movimiento import MovimientoCreateSalida

    with pytest.raises(ValidationError):
        MovimientoCreateSalida(
            producto_codigo="PROD-001", cantidad=5, proveedor_codigo="PROV-001"
        )  # type: ignore


def test_movimiento_response_y_historial_query():
    from app.schemas.movimiento import MovimientoResponse, HistorialQuery

    obj = MovimientoResponse(
        id=1,
        producto_codigo="PROD-001",
        proveedor_codigo="PROV-001",
        tipo="entrada",
        cantidad=10,
        motivo="Test",
        fecha="2026-09-08T11:00:00Z",
    )
    assert obj.tipo == "entrada"
    # HistorialQuery tipo filtro
    q = HistorialQuery(tipo="entrada")
    assert q.tipo == "entrada"
    with pytest.raises(ValidationError):
        HistorialQuery(tipo="invalido")  # type: ignore
    q2 = HistorialQuery(producto_codigo="  prod-001 ")
    assert q2.producto_codigo == "PROD-001"


def test_stock_response():
    from app.schemas.movimiento import StockResponse

    obj = StockResponse(
        codigo="PROD-001",
        nombre="Test",
        stock_inicial=5,
        entradas=10,
        salidas=3,
        stock_actual=12,
    )
    assert obj.stock_actual == 12
    assert obj.entradas == 10
