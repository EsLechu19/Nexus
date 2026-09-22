"""Tests de T05 — Service listar_historial y calcular_stock (RF-3, RF-4)."""

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


def test_listar_historial_vacio():
    """RF-3: sin movimientos -> []"""
    from app.services.movimiento_service import listar_historial

    db = _make_session()
    assert listar_historial(db) == []
    db.close()


def test_listar_historial_orden_y_filtros():
    """RF-3: orden fecha DESC, filtros producto y tipo."""
    from app.services.movimiento_service import (
        listar_historial,
        registrar_entrada,
        registrar_salida,
    )

    db = _make_session()
    _crear_producto(db, codigo="PROD-001", stock_inicial=0)
    _crear_producto(db, codigo="PROD-002", stock_inicial=0)
    _crear_proveedor(db, codigo="PROV-001")
    # Crear movimientos para PROD-001: entrada 5, salida 2, entrada 3
    registrar_entrada(
        db,
        MovimientoCreateEntrada(
            producto_codigo="PROD-001", proveedor_codigo="PROV-001", cantidad=5
        ),
    )
    registrar_salida(db, MovimientoCreateSalida(producto_codigo="PROD-001", cantidad=2))
    registrar_entrada(
        db,
        MovimientoCreateEntrada(
            producto_codigo="PROD-001", proveedor_codigo="PROV-001", cantidad=3
        ),
    )
    # Para PROD-002: entrada 7
    registrar_entrada(
        db,
        MovimientoCreateEntrada(
            producto_codigo="PROD-002", proveedor_codigo="PROV-001", cantidad=7
        ),
    )

    # Sin filtros -> 4 movimientos ordenados DESC (último primero) (sin entrada_inicial ya que stock_inicial=0)
    historial = listar_historial(db)
    assert len(historial) == 4
    # Orden por fecha DESC, id DESC: el último creado debe ser primero
    assert (
        historial[0].cantidad == 7
        and historial[0].producto_id
        == db.query(__import__("app.models.producto", fromlist=["Producto"]).Producto)
        .filter_by(sku="PROD-002")
        .first()
        .id
    )

    # Filtro producto
    hist_prod1 = listar_historial(db, producto_codigo="PROD-001")
    assert len(hist_prod1) == 3
    assert all(
        m.producto_id
        == db.query(__import__("app.models.producto", fromlist=["Producto"]).Producto)
        .filter_by(sku="PROD-001")
        .first()
        .id
        for m in hist_prod1
    )

    # Filtro tipo entrada
    hist_entradas = listar_historial(db, tipo="entrada")
    assert len(hist_entradas) == 3  # 2 de PROD-001 +1 de PROD-002
    assert all(m.tipo == "entrada" for m in hist_entradas)

    # Filtro ambos
    hist_prod1_entradas = listar_historial(
        db, producto_codigo="PROD-001", tipo="entrada"
    )
    assert len(hist_prod1_entradas) == 2
    db.close()


def test_listar_historial_producto_no_existe_404():
    """RF-3: filtro producto inexistente -> 404."""
    from fastapi import HTTPException

    from app.services.movimiento_service import listar_historial

    db = _make_session()
    with pytest.raises(HTTPException) as exc:
        listar_historial(db, producto_codigo="NOPE")
    assert exc.value.status_code == 404
    db.close()


def test_listar_historial_tipo_invalido_422_schema():
    """RF-3: tipo inválido -> 422 en schema (no en service)."""
    from pydantic import ValidationError

    from app.schemas.movimiento import HistorialQuery

    with pytest.raises(ValidationError):
        HistorialQuery(tipo="invalido")  # type: ignore


def test_calcular_stock_sin_movimientos():
    """RF-4: sin movimientos -> stock_inicial."""
    from app.services.movimiento_service import calcular_stock

    db = _make_session()
    _crear_producto(db, codigo="PROD-003", stock_inicial=8)
    stock = calcular_stock(db, "PROD-003")
    assert stock["stock_actual"] == 8
    assert stock["entradas"] == 0 and stock["salidas"] == 0
    db.close()


def test_calcular_stock_con_movimientos():
    """RF-4: inicial 5 + entradas 10 - salidas 3 = 12."""
    from app.services.movimiento_service import (
        calcular_stock,
        registrar_entrada,
        registrar_salida,
    )

    db = _make_session()
    _crear_producto(db, codigo="PROD-004", stock_inicial=5)
    _crear_proveedor(db, codigo="PROV-004")
    registrar_entrada(
        db,
        MovimientoCreateEntrada(
            producto_codigo="PROD-004", proveedor_codigo="PROV-004", cantidad=10
        ),
    )
    registrar_salida(db, MovimientoCreateSalida(producto_codigo="PROD-004", cantidad=3))
    stock = calcular_stock(db, "PROD-004")
    assert stock["stock_actual"] == 12
    assert stock["entradas"] == 10
    assert stock["salidas"] == 3
    db.close()


def test_calcular_stock_excluye_entrada_inicial():
    """RF-4: entrada_inicial no se cuenta como entrada."""
    from app.models.movimiento_inventario import MovimientoInventario
    from app.services.movimiento_service import calcular_stock

    db = _make_session()
    prod = _crear_producto(db, codigo="PROD-005", stock_inicial=5)
    # Simular entrada_inicial residual de 001 (si existe)
    # Crear manualmente una entrada_inicial y verificar que no se cuenta
    mov_inicial = MovimientoInventario(
        producto_id=prod.id,
        proveedor_id=None,
        tipo="entrada_inicial",
        cantidad=5,
        motivo=None,
    )
    db.add(mov_inicial)
    db.commit()
    stock = calcular_stock(db, "PROD-005")
    # Debe seguir siendo 5 inicial, no 10 (inicial + entrada_inicial)
    assert stock["stock_actual"] == 5
    assert stock["entradas"] == 0
    db.close()


def test_listar_stock_global_solo_activos():
    """RF-4: global solo activos ordenados por codigo."""
    from app.services.movimiento_service import listar_stock

    db = _make_session()
    _crear_producto(db, codigo="PROD-006", stock_inicial=1)
    _crear_producto(db, codigo="PROD-007", stock_inicial=2)
    prod_inactivo = _crear_producto(db, codigo="PROD-008", stock_inicial=3)
    prod_inactivo.estado = "inactivo"
    db.commit()

    stocks = listar_stock(db)
    assert [s["codigo"] for s in stocks] == ["PROD-006", "PROD-007"]
    assert all(s["codigo"] != "PROD-008" for s in stocks)

    # Con incluir_inactivos
    stocks_all = listar_stock(db, incluir_inactivos=True)
    assert len(stocks_all) == 3
    db.close()


def test_calcular_stock_no_existe_404():
    from fastapi import HTTPException

    from app.services.movimiento_service import calcular_stock

    db = _make_session()
    with pytest.raises(HTTPException) as exc:
        calcular_stock(db, "NOPE")
    assert exc.value.status_code == 404
    db.close()
