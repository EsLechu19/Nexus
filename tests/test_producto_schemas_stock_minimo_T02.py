"""Tests de T02 004 — Schemas stock_minimo y StockResponse (RF-1)."""

import pytest
from pydantic import ValidationError


def test_producto_create_con_stock_minimo_valido():
    from app.schemas.producto import ProductoCreate

    obj = ProductoCreate(
        sku="SKU-001",
        nombre="Test",
        categoria="videojuego",
        stock_inicial=5,
        stock_minimo=10,
    )
    assert obj.stock_minimo == 10
    obj2 = ProductoCreate(
        sku="SKU-002", nombre="Test", categoria="consola", stock_minimo=0
    )
    assert obj2.stock_minimo == 0


def test_producto_create_stock_minimo_default_y_null():
    from app.schemas.producto import ProductoCreate

    obj = ProductoCreate(sku="SKU-003", nombre="Test", categoria="videojuego")
    assert obj.stock_minimo == 0
    obj2 = ProductoCreate(
        sku="SKU-004", nombre="Test", categoria="videojuego", stock_minimo=None
    )  # type: ignore
    assert obj2.stock_minimo == 0


def test_producto_create_stock_minimo_validaciones():
    from app.schemas.producto import ProductoCreate

    for invalido in ["", -5, "10", 1.5, 1000001, -1]:
        with pytest.raises(ValidationError):
            ProductoCreate(
                sku="SKU-005",
                nombre="Test",
                categoria="videojuego",
                stock_minimo=invalido,
            )  # type: ignore


def test_producto_update_con_stock_minimo():
    from app.schemas.producto import ProductoUpdate

    obj = ProductoUpdate(nombre="Nuevo", stock_minimo=5)  # type: ignore
    assert obj.stock_minimo == 5  # type: ignore
    obj2 = ProductoUpdate(nombre="Nuevo", stock_minimo=None)  # type: ignore
    assert (
        obj2.stock_minimo is None or obj2.stock_minimo == 0
    )  # null debe ser permitido para borrar?


def test_producto_response_con_stock_minimo():
    from app.schemas.producto import ProductoResponse

    obj = ProductoResponse(
        sku="SKU-006",
        nombre="Test",
        categoria="videojuego",
        stock_inicial=5,
        stock_minimo=10,
        estado="activo",
    )
    assert obj.stock_minimo == 10  # type: ignore


def test_stock_response_con_alerta():
    from app.schemas.stock import StockResponse

    obj = StockResponse(
        codigo="PROD-001",
        nombre="Test",
        stock_inicial=5,
        stock_minimo=10,
        entradas=0,
        salidas=0,
        stock_actual=5,
        alerta=True,
    )
    assert obj.alerta is True
    assert obj.codigo == "PROD-001"


def test_stock_response_codigo_normalizacion():
    # StockResponse no necesita validar codigo, pero StockQuery sí
    from app.schemas.stock import StockQuery  # type: ignore

    q = StockQuery(codigo="  prod-001 ")
    assert q.codigo == "PROD-001"
