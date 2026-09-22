"""Tests de T06 — Service listar_activos y obtener_por_sku (RF-2, RF-3)."""

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


def _crear(db, sku, nombre="Producto Test", categoria="videojuego", stock_inicial=0):
    from app.services.producto_service import crear_producto

    return crear_producto(
        db,
        ProductoCreate(
            sku=sku, nombre=nombre, categoria=categoria, stock_inicial=stock_inicial
        ),
    )


def test_listar_activos_vacio():
    """RF-2: sin productos -> lista vacía."""
    from app.services.producto_service import listar_activos

    db = _make_session()
    assert listar_activos(db) == []
    db.close()


def test_listar_activos_solo_activos():
    """RF-2: devuelve solo activos con sku, nombre, categoria, stock_inicial."""
    from app.services.producto_service import listar_activos

    db = _make_session()
    _crear(db, "SKU-001", nombre="Juego A", categoria="videojuego", stock_inicial=5)
    _crear(db, "SKU-002", nombre="Consola B", categoria="consola", stock_inicial=0)
    prod_inactivo = _crear(db, "SKU-003", nombre="Accesorio C", categoria="accesorio")
    prod_inactivo.estado = "inactivo"
    db.commit()

    activos = listar_activos(db)
    skus = {p.sku for p in activos}
    assert skus == {"SKU-001", "SKU-002"}
    for p in activos:
        assert p.estado == "activo"
        assert (
            hasattr(p, "sku")
            and hasattr(p, "nombre")
            and hasattr(p, "categoria")
            and hasattr(p, "stock_inicial")
        )
    db.close()


def test_obtener_por_sku_activo_detalle():
    """RF-3: detalle de activo incluye estado activo."""
    from app.services.producto_service import obtener_por_sku

    db = _make_session()
    _crear(db, "SKU-010", nombre="Zelda", categoria="videojuego", stock_inicial=7)
    prod = obtener_por_sku(db, "SKU-010")
    assert prod.sku == "SKU-010"
    assert prod.nombre == "Zelda"
    assert prod.categoria == "videojuego"
    assert prod.stock_inicial == 7
    assert prod.estado == "activo"
    db.close()


def test_obtener_por_sku_inactivo_trazabilidad():
    """RF-3: detalle incluye inactivos para trazabilidad."""
    from app.services.producto_service import obtener_por_sku

    db = _make_session()
    prod = _crear(db, "SKU-011", nombre="Baja", categoria="consola")
    prod.estado = "inactivo"
    db.commit()

    fetched = obtener_por_sku(db, "SKU-011")
    assert fetched.estado == "inactivo"
    assert fetched.sku == "SKU-011"
    db.close()


def test_obtener_por_sku_normalizado():
    """RF-3: SKU normalizado trim+upper en consulta."""
    from app.services.producto_service import obtener_por_sku

    db = _make_session()
    _crear(db, "SKU-012", nombre="Test", categoria="accesorio")
    prod = obtener_por_sku(db, "  sku-012 ")
    assert prod.sku == "SKU-012"
    db.close()


def test_obtener_por_sku_no_existe_404():
    """RF-3: SKU inexistente -> 404."""
    from fastapi import HTTPException

    from app.services.producto_service import obtener_por_sku

    db = _make_session()
    with pytest.raises(HTTPException) as exc:
        obtener_por_sku(db, "NO-EXISTE")
    assert exc.value.status_code == 404
    assert "no encontrado" in exc.value.detail.lower()
    db.close()
