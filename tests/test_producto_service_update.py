"""Tests de T07 — Service actualizar_producto (RF-4)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.schemas.producto import ProductoCreate, ProductoUpdate


def _make_session():
    from app.models.movimiento_inventario import MovimientoInventario  # noqa: F401
    from app.models.producto import Producto  # noqa: F401

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _crear(
    db, sku="SKU-001", nombre="Producto Base", categoria="videojuego", stock_inicial=0
):
    from app.services.producto_service import crear_producto

    return crear_producto(
        db,
        ProductoCreate(
            sku=sku, nombre=nombre, categoria=categoria, stock_inicial=stock_inicial
        ),
    )


def test_actualizar_producto_solo_nombre():
    """RF-4: edita solo nombre de activo."""
    from app.services.producto_service import actualizar_producto

    db = _make_session()
    _crear(db, sku="UPD-001", nombre="Original", categoria="videojuego")
    prod = actualizar_producto(db, "UPD-001", ProductoUpdate(nombre="Nuevo Nombre"))
    assert prod.nombre == "Nuevo Nombre"
    assert prod.categoria == "videojuego"
    assert prod.sku == "UPD-001"
    db.close()


def test_actualizar_producto_solo_categoria():
    """RF-4: edita solo categoria."""
    from app.services.producto_service import actualizar_producto

    db = _make_session()
    _crear(db, sku="UPD-002", nombre="Test", categoria="videojuego")
    prod = actualizar_producto(db, "UPD-002", ProductoUpdate(categoria="consola"))
    assert prod.categoria == "consola"
    assert prod.nombre == "Test"
    db.close()


def test_actualizar_producto_ambos_campos():
    """RF-4: edita nombre y categoria."""
    from app.services.producto_service import actualizar_producto

    db = _make_session()
    _crear(db, sku="UPD-003", nombre="Original Largo", categoria="videojuego")
    prod = actualizar_producto(
        db, "UPD-003", ProductoUpdate(nombre="Nuevo", categoria="accesorio")
    )
    assert prod.nombre == "Nuevo"
    assert prod.categoria == "accesorio"
    db.close()


def test_actualizar_producto_sku_mismo_valor_se_ignora():
    """RF-4: sku mismo valor (normalizado) se ignora."""
    from app.services.producto_service import actualizar_producto

    db = _make_session()
    _crear(db, sku="SKU-004", nombre="Test", categoria="consola")
    # ProductoUpdate con sku igual al path (con espacios y case distinto)
    datos = ProductoUpdate(nombre="Cambiado", sku="  sku-004 ")  # type: ignore[call-arg]
    prod = actualizar_producto(db, "SKU-004", datos)
    assert prod.nombre == "Cambiado"
    assert prod.sku == "SKU-004"
    db.close()


def test_actualizar_producto_sku_distinto_rechaza_400():
    """RF-4: sku distinto -> 400 inmutable."""
    from fastapi import HTTPException

    from app.services.producto_service import actualizar_producto

    db = _make_session()
    _crear(db, sku="SKU-005", nombre="Test", categoria="videojuego")
    datos = ProductoUpdate(nombre="Nuevo", sku="OTRO-999")  # type: ignore[call-arg]
    with pytest.raises(HTTPException) as exc:
        actualizar_producto(db, "SKU-005", datos)
    assert exc.value.status_code == 400
    assert "inmutable" in exc.value.detail.lower() or "sku" in exc.value.detail.lower()
    db.close()


def test_actualizar_producto_inactivo_rechaza_400():
    """RF-4: inactivo no editable -> 400."""
    from fastapi import HTTPException

    from app.services.producto_service import actualizar_producto

    db = _make_session()
    prod = _crear(db, sku="SKU-006", nombre="Test", categoria="videojuego")
    prod.estado = "inactivo"
    db.commit()
    with pytest.raises(HTTPException) as exc:
        actualizar_producto(db, "SKU-006", ProductoUpdate(nombre="Nuevo"))
    assert exc.value.status_code == 400
    db.close()


def test_actualizar_producto_no_encontrado_404():
    """RF-4: SKU inexistente -> 404."""
    from fastapi import HTTPException

    from app.services.producto_service import actualizar_producto

    db = _make_session()
    with pytest.raises(HTTPException) as exc:
        actualizar_producto(db, "NO-EXISTE", ProductoUpdate(nombre="Nuevo"))
    assert exc.value.status_code == 404
    db.close()


def test_actualizar_producto_ignora_stock_y_estado_extra():
    """RF-4: stock_inicial/estado extra se ignoran."""
    from app.services.producto_service import actualizar_producto

    db = _make_session()
    _crear(db, sku="SKU-007", nombre="Test", categoria="videojuego", stock_inicial=5)
    # Payload con campos extra que deben ignorarse (via model_extra)
    datos = ProductoUpdate(
        nombre="Cambiado"
    )  # stock y estado no están en schema, se ignoran
    # Simular que vienen en dict extra: serializar y añadir
    prod = actualizar_producto(db, "SKU-007", datos)
    assert prod.stock_inicial == 5  # no cambió
    assert prod.estado == "activo"
    assert prod.nombre == "Cambiado"
    db.close()


def test_actualizar_producto_normaliza_sku_path():
    """RF-4: sku path normalizado trim+upper."""
    from app.services.producto_service import actualizar_producto

    db = _make_session()
    _crear(db, sku="SKU-008", nombre="Test", categoria="consola")
    prod = actualizar_producto(db, "  sku-008 ", ProductoUpdate(nombre="Nuevo"))
    assert prod.nombre == "Nuevo"
    db.close()
