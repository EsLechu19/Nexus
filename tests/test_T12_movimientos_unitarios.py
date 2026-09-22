"""Tests de T12 — Unitarios de service movimientos (mock + sqlite, concurrencia) RF-1..RF-4."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.schemas.movimiento import MovimientoCreateEntrada, MovimientoCreateSalida
from app.schemas.producto import ProductoCreate
from app.schemas.proveedor import ProveedorCreate


def _make_session():
    from app.models.producto import Producto  # noqa: F401
    from app.models.proveedor import Proveedor  # noqa: F401
    from app.models.movimiento_inventario import MovimientoInventario  # noqa: F401

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def _crear_producto_proveedor(
    SessionLocal, prod_codigo="PROD-001", prov_codigo="PROV-001", stock_inicial=10
):
    from app.services.producto_service import crear_producto
    from app.services.proveedor_service import crear_proveedor

    db = SessionLocal()
    crear_producto(
        db,
        ProductoCreate(
            sku=prod_codigo,
            nombre="Producto Test",
            categoria="videojuego",
            stock_inicial=stock_inicial,
        ),
    )
    crear_proveedor(db, ProveedorCreate(codigo=prov_codigo, nombre="Proveedor Test"))
    db.close()


def test_T12_entrada_con_sin_motivo_y_proveedor_normalizado():
    from app.services.movimiento_service import registrar_entrada

    SessionLocal = _make_session()
    _crear_producto_proveedor(
        SessionLocal, prod_codigo="PROD-001", prov_codigo="PROV-001"
    )
    db = SessionLocal()
    mov = registrar_entrada(
        db,
        MovimientoCreateEntrada(
            producto_codigo="PROD-001",
            proveedor_codigo="PROV-001",
            cantidad=5,
            motivo="Compra",
        ),
    )
    assert mov.motivo == "Compra"
    mov2 = registrar_entrada(
        db,
        MovimientoCreateEntrada(
            producto_codigo="  prod-001 ", proveedor_codigo="  prov-001 ", cantidad=1
        ),
    )
    assert mov2.motivo is None
    db.close()


def test_T12_salida_stock_suficiente_e_insuficiente():
    from app.services.movimiento_service import registrar_entrada, registrar_salida
    from fastapi import HTTPException

    SessionLocal = _make_session()
    _crear_producto_proveedor(SessionLocal, prod_codigo="PROD-002", stock_inicial=10)
    db = SessionLocal()
    registrar_entrada(
        db,
        MovimientoCreateEntrada(
            producto_codigo="PROD-002", proveedor_codigo="PROV-001", cantidad=5
        ),
    )
    # stock 15, salida 10 -> ok
    mov = registrar_salida(
        db, MovimientoCreateSalida(producto_codigo="PROD-002", cantidad=10)
    )
    assert mov.tipo == "salida"
    # stock ahora 5, salida 6 -> 400
    with pytest.raises(HTTPException) as exc:
        registrar_salida(
            db, MovimientoCreateSalida(producto_codigo="PROD-002", cantidad=6)
        )
    assert exc.value.status_code == 400
    db.close()


def test_T12_cantidad_0_negativa_decimal_mayor1M():
    from pydantic import ValidationError
    from app.schemas.movimiento import MovimientoCreateEntrada

    for invalido in [0, -1, 1000001, 1.5, "10"]:
        with pytest.raises(ValidationError):
            MovimientoCreateEntrada(
                producto_codigo="PROD-001",
                proveedor_codigo="PROV-001",
                cantidad=invalido,
            )  # type: ignore


def test_T12_motivo_vacio_1_201_salto():
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


def test_T12_producto_proveedor_no_existe_inactivo():
    from fastapi import HTTPException
    from app.services.movimiento_service import registrar_entrada

    SessionLocal = _make_session()
    _crear_producto_proveedor(
        SessionLocal, prod_codigo="PROD-003", prov_codigo="PROV-003"
    )
    db = SessionLocal()
    # producto no existe
    with pytest.raises(HTTPException) as exc:
        registrar_entrada(
            db,
            MovimientoCreateEntrada(
                producto_codigo="NOPE", proveedor_codigo="PROV-003", cantidad=1
            ),
        )
    assert exc.value.status_code == 404
    # proveedor no existe
    with pytest.raises(HTTPException) as exc:
        registrar_entrada(
            db,
            MovimientoCreateEntrada(
                producto_codigo="PROD-003", proveedor_codigo="NOPE", cantidad=1
            ),
        )
    assert exc.value.status_code == 404
    # producto inactivo
    from app.models.producto import Producto

    prod = db.query(Producto).filter(Producto.sku == "PROD-003").first()
    prod.estado = "inactivo"
    db.commit()
    with pytest.raises(HTTPException) as exc:
        registrar_entrada(
            db,
            MovimientoCreateEntrada(
                producto_codigo="PROD-003", proveedor_codigo="PROV-003", cantidad=1
            ),
        )
    assert exc.value.status_code == 400
    db.close()
    # proveedor inactivo
    SessionLocal2 = _make_session()
    _crear_producto_proveedor(
        SessionLocal2, prod_codigo="PROD-004", prov_codigo="PROV-004"
    )
    db2 = SessionLocal2()
    from app.models.proveedor import Proveedor

    prov = db2.query(Proveedor).filter(Proveedor.codigo == "PROV-004").first()
    prov.estado = "inactivo"
    db2.commit()
    with pytest.raises(HTTPException) as exc:
        registrar_entrada(
            db2,
            MovimientoCreateEntrada(
                producto_codigo="PROD-004", proveedor_codigo="PROV-004", cantidad=1
            ),
        )
    assert exc.value.status_code == 400
    db2.close()


def test_T12_proveedor_enviado_en_salida_422():
    from pydantic import ValidationError
    from app.schemas.movimiento import MovimientoCreateSalida

    with pytest.raises(ValidationError):
        MovimientoCreateSalida(
            producto_codigo="PROD-001", cantidad=1, proveedor_codigo="PROV-001"
        )  # type: ignore


def test_T12_historial_filtrado_y_orden():
    from app.services.movimiento_service import (
        registrar_entrada,
        registrar_salida,
        listar_historial,
    )

    SessionLocal = _make_session()
    _crear_producto_proveedor(SessionLocal, prod_codigo="PROD-005", stock_inicial=0)
    db = SessionLocal()
    # Crear otro producto en el mismo engine (reutilizar db)
    from app.services.producto_service import crear_producto

    try:
        crear_producto(
            db,
            ProductoCreate(
                sku="PROD-006", nombre="Otro", categoria="consola", stock_inicial=0
            ),
        )
    except Exception:
        pass
    db.close()
    # Usaremos un solo engine para todo el test
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal3 = sessionmaker(bind=engine)
    db3 = SessionLocal3()
    from app.services.producto_service import crear_producto as cp
    from app.services.proveedor_service import crear_proveedor as cpr

    cp(
        db3,
        ProductoCreate(
            sku="PROD-005",
            nombre="Producto Test",
            categoria="videojuego",
            stock_inicial=0,
        ),
    )
    cpr(db3, ProveedorCreate(codigo="PROV-005", nombre="Proveedor Test"))
    try:
        cp(
            db3,
            ProductoCreate(
                sku="PROD-006", nombre="Otro", categoria="consola", stock_inicial=0
            ),
        )
    except Exception:
        pass
    db3.close()
    db4 = SessionLocal3()
    registrar_entrada(
        db4,
        MovimientoCreateEntrada(
            producto_codigo="PROD-005", proveedor_codigo="PROV-005", cantidad=5
        ),
    )
    registrar_salida(
        db4, MovimientoCreateSalida(producto_codigo="PROD-005", cantidad=2)
    )
    historial = listar_historial(db4)
    assert len(historial) == 2
    assert historial[0].created_at >= historial[1].created_at  # DESC
    # Filtro producto
    hist_prod = listar_historial(db4, producto_codigo="PROD-005")
    assert len(hist_prod) == 2
    # Filtro tipo
    hist_entrada = listar_historial(db4, tipo="entrada")
    assert all(m.tipo == "entrada" for m in hist_entrada)
    db4.close()


def test_T12_stock_recalculado():
    from app.services.movimiento_service import (
        registrar_entrada,
        registrar_salida,
        calcular_stock,
    )

    SessionLocal = _make_session()
    _crear_producto_proveedor(SessionLocal, prod_codigo="PROD-007", stock_inicial=5)
    db = SessionLocal()
    registrar_entrada(
        db,
        MovimientoCreateEntrada(
            producto_codigo="PROD-007", proveedor_codigo="PROV-001", cantidad=10
        ),
    )
    registrar_salida(db, MovimientoCreateSalida(producto_codigo="PROD-007", cantidad=3))
    stock = calcular_stock(db, "PROD-007")
    assert stock["stock_actual"] == 12
    assert stock["entradas"] == 10
    db.close()


def test_T12_concurrencia_dos_salidas_exceden_stock():
    """Dos salidas secuenciales que exceden stock: una 201 otra 400 (simula concurrencia con FOR UPDATE)."""
    from fastapi import HTTPException
    from app.services.movimiento_service import registrar_salida

    SessionLocal = _make_session()
    _crear_producto_proveedor(SessionLocal, prod_codigo="PROD-008", stock_inicial=10)
    db = SessionLocal()
    # Primera salida 8 -> stock 2
    registrar_salida(db, MovimientoCreateSalida(producto_codigo="PROD-008", cantidad=8))
    # Segunda salida 8 con stock 2 -> debe fallar 400
    with pytest.raises(HTTPException) as exc:
        registrar_salida(
            db, MovimientoCreateSalida(producto_codigo="PROD-008", cantidad=8)
        )
    assert exc.value.status_code == 400
    # Verificar stock no negativo
    from app.services.movimiento_service import calcular_stock

    stock = calcular_stock(db, "PROD-008")
    assert stock["stock_actual"] == 2
    db.close()
