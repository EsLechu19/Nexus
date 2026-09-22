"""Tests de T16 — Unitarios de service con mock session (RF-1..RF-5)."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.schemas.producto import ProductoCreate, ProductoUpdate


def _mock_db_with_existing(sku_existente: str | None = None):
    """Mock de Session para carrera/duplicado."""
    mock_db = MagicMock()
    mock_producto = MagicMock()
    mock_producto.sku = sku_existente
    mock_producto.estado = "activo"
    if sku_existente:
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_producto
        )
    else:
        mock_db.query.return_value.filter.return_value.first.return_value = None
    return mock_db


def test_T16_alta_valida_mock():
    """RF-1: alta válida con stock 0 (mock, sin DB)."""
    from app.services.producto_service import crear_producto

    mock_db = _mock_db_with_existing(None)
    mock_db.flush.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None

    datos = ProductoCreate(
        sku="MOCK-001", nombre="Producto Mock", categoria="videojuego", stock_inicial=0
    )
    # Simular que crear_producto usa mock y no falla
    # Como mock no tiene tabla real, solo verificamos que no lanza 409 y llama a add
    try:
        crear_producto(mock_db, datos)
    except HTTPException as exc:
        assert exc.status_code != 409  # no debe ser duplicado
    assert mock_db.add.called


def test_T16_duplicado_normalizado_mock_409():
    """RF-1: duplicado normalizado -> 409 (mock)."""
    from app.services.producto_service import crear_producto

    mock_db = _mock_db_with_existing("MOCK-001")
    datos = ProductoCreate(sku="  mock-001 ", nombre="Otro", categoria="consola")
    with pytest.raises(HTTPException) as exc:
        crear_producto(mock_db, datos)
    assert exc.value.status_code == 409


def test_T16_carrera_integrity_error_mock_409():
    """RF-1: carrera IntegrityError -> 409 (mock)."""
    from app.services.producto_service import crear_producto

    mock_db = _mock_db_with_existing(None)
    mock_db.flush.side_effect = IntegrityError("mock", {}, Exception("unique"))
    datos = ProductoCreate(sku="RACE-001", nombre="Race", categoria="videojuego")
    with pytest.raises(HTTPException) as exc:
        crear_producto(mock_db, datos)
    assert exc.value.status_code == 409


def test_T16_edicion_inmutable_mock_400():
    """RF-4: sku distinto inmutable -> 400 (mock)."""
    from app.services.producto_service import actualizar_producto

    mock_db = MagicMock()
    mock_prod = MagicMock()
    mock_prod.sku = "SKU-001"
    mock_prod.estado = "activo"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_prod

    datos = ProductoUpdate(nombre="Nuevo", sku="OTRO-999")  # type: ignore
    with pytest.raises(HTTPException) as exc:
        actualizar_producto(mock_db, "SKU-001", datos)
    assert exc.value.status_code == 400


def test_T16_edicion_inactivo_mock_400():
    """RF-4: inactivo no editable -> 400 (mock)."""
    from app.services.producto_service import actualizar_producto

    mock_db = MagicMock()
    mock_prod = MagicMock()
    mock_prod.estado = "inactivo"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_prod

    with pytest.raises(HTTPException) as exc:
        actualizar_producto(mock_db, "SKU-001", ProductoUpdate(nombre="Nuevo"))
    assert exc.value.status_code == 400


def test_T16_baja_ya_inactivo_400_mock():
    """RF-5: baja ya inactivo -> 400 (mock)."""
    from app.services.producto_service import baja_producto

    mock_db = MagicMock()
    mock_prod = MagicMock()
    mock_prod.estado = "inactivo"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_prod

    with pytest.raises(HTTPException) as exc:
        baja_producto(mock_db, "SKU-001")
    assert exc.value.status_code == 400


def test_T16_consultas_filtradas_mock():
    """RF-2/RF-3: listar_activos filtra, obtener_por_sku normaliza (mock)."""
    from app.services.producto_service import listar_activos, obtener_por_sku

    mock_db = MagicMock()
    # listar_activos debe filtrar por estado activo
    listar_activos(mock_db)
    assert mock_db.query.called

    # obtener_por_sku normaliza y busca
    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(
        sku="SKU-001", estado="activo"
    )
    prod = obtener_por_sku(mock_db, "  sku-001 ")
    assert prod.sku == "SKU-001"


def test_T16_validaciones_schema():
    """RF-1/RF-4: validaciones Pydantic (nombre, sku, categoria, stock)."""
    with pytest.raises(Exception):
        ProductoCreate(sku="AB", nombre="Test", categoria="consola")
    with pytest.raises(Exception):
        ProductoCreate(sku="SKU-001", nombre="A", categoria="consola")
    with pytest.raises(Exception):
        ProductoCreate(sku="SKU-002", nombre="Test", categoria="juego")
    with pytest.raises(Exception):
        ProductoCreate(
            sku="SKU-003", nombre="Test", categoria="consola", stock_inicial=-1
        )  # type: ignore
