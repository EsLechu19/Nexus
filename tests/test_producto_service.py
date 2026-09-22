"""Tests de T05 — Service crear_producto (RF-1)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.schemas.producto import ProductoCreate


def _make_session():
    """Crea DB en memoria con tablas de catálogo."""
    # Importar modelos para registrar en Base.metadata
    from app.models.producto import Producto  # noqa: F401
    from app.models.movimiento_inventario import MovimientoInventario  # noqa: F401

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_crear_producto_valido_sin_stock_no_genera_movimiento():
    """RF-1: alta con stock 0 no genera traza."""
    from app.services.producto_service import crear_producto

    db = _make_session()
    datos = ProductoCreate(
        sku="SKU-001", nombre="Juego A", categoria="videojuego", stock_inicial=0
    )
    prod = crear_producto(db, datos)

    assert prod.sku == "SKU-001"
    assert prod.estado == "activo"
    assert prod.stock_inicial == 0

    from app.models.movimiento_inventario import MovimientoInventario

    assert db.query(MovimientoInventario).count() == 0
    db.close()


def test_crear_producto_valido_con_stock_genera_traza():
    """RF-1: alta con stock >0 genera movimiento entrada_inicial."""
    from app.services.producto_service import crear_producto
    from app.models.movimiento_inventario import MovimientoInventario

    db = _make_session()
    datos = ProductoCreate(
        sku="SKU-002", nombre="Consola X", categoria="consola", stock_inicial=10
    )
    prod = crear_producto(db, datos)

    assert prod.stock_inicial == 10
    movs = db.query(MovimientoInventario).all()
    assert len(movs) == 1
    assert movs[0].producto_id == prod.id
    assert movs[0].tipo == "entrada_inicial"
    assert movs[0].cantidad == 10
    db.close()


def test_crear_producto_stock_none_default_0():
    """RF-1: stock_inicial None/omitido -> 0 sin traza."""
    from app.services.producto_service import crear_producto
    from app.models.movimiento_inventario import MovimientoInventario

    db = _make_session()
    datos = ProductoCreate(sku="SKU-003", nombre="Accesorio", categoria="accesorio")
    prod = crear_producto(db, datos)
    assert prod.stock_inicial == 0
    assert db.query(MovimientoInventario).count() == 0
    db.close()


def test_crear_producto_normaliza_sku_y_categoria():
    """RF-1: sku trim+upper, categoria trim+lower."""
    from app.services.producto_service import crear_producto

    db = _make_session()
    datos = ProductoCreate(
        sku="  ps5-slim-001 ", nombre="Test", categoria="  Consola ", stock_inicial=0
    )
    prod = crear_producto(db, datos)
    assert prod.sku == "PS5-SLIM-001"
    assert prod.categoria == "consola"
    db.close()


def test_crear_producto_rechaza_duplicado_exacto_409():
    """RF-1: SKU duplicado -> 409, incluye inactivos."""
    from fastapi import HTTPException
    from app.services.producto_service import crear_producto

    db = _make_session()
    datos1 = ProductoCreate(sku="DUPL-001", nombre="Producto A", categoria="videojuego")
    crear_producto(db, datos1)

    datos2 = ProductoCreate(sku="DUPL-001", nombre="Producto B", categoria="consola")
    with pytest.raises(HTTPException) as exc:
        crear_producto(db, datos2)
    assert exc.value.status_code == 409
    assert "ya existe" in exc.value.detail.lower()
    db.close()


def test_crear_producto_rechaza_duplicado_normalizado_409():
    """RF-1: duplicado tras normalización (case/espacios) -> 409."""
    from fastapi import HTTPException
    from app.services.producto_service import crear_producto

    db = _make_session()
    crear_producto(
        db, ProductoCreate(sku="ABC-001", nombre="Producto A", categoria="videojuego")
    )
    with pytest.raises(HTTPException) as exc:
        crear_producto(
            db,
            ProductoCreate(sku="  abc-001 ", nombre="Producto B", categoria="consola"),
        )
    assert exc.value.status_code == 409
    db.close()


def test_crear_producto_rechaza_duplicado_inactivo_409():
    """RNF-3: SKU de producto inactivo no reutilizable."""
    from fastapi import HTTPException
    from app.services.producto_service import crear_producto

    db = _make_session()
    prod = crear_producto(
        db, ProductoCreate(sku="INACT-001", nombre="Producto A", categoria="videojuego")
    )
    # simular baja lógica
    prod.estado = "inactivo"
    db.commit()

    with pytest.raises(HTTPException) as exc:
        crear_producto(
            db,
            ProductoCreate(sku="INACT-001", nombre="Producto B", categoria="consola"),
        )
    assert exc.value.status_code == 409
    db.close()


def test_crear_producto_captura_integrity_error_409():
    """RF-1: carrera por IntegrityError -> 409."""
    from unittest.mock import MagicMock
    from sqlalchemy.exc import IntegrityError
    from fastapi import HTTPException
    from app.services.producto_service import crear_producto
    from app.schemas.producto import ProductoCreate

    # Mock de session que falla en commit por unique violation
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    # Simular que add/flush/commit lanza IntegrityError
    mock_db.commit.side_effect = IntegrityError("mock", {}, Exception("unique"))
    mock_db.flush.side_effect = IntegrityError("mock", {}, Exception("unique"))

    datos = ProductoCreate(sku="RACE-001", nombre="Race", categoria="videojuego")
    with pytest.raises(HTTPException) as exc:
        crear_producto(mock_db, datos)
    assert exc.value.status_code == 409
