"""Tests de T14 — Unitarios de service Proveedores (mock + sqlite) RF-1..RF-5."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.schemas.proveedor import ProveedorCreate, ProveedorUpdate


def _make_session():
    from app.models.proveedor import Proveedor  # noqa: F401

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


# RF-1: alta con/sin contacto
def test_T14_alta_sin_contacto_sqlite():
    from app.services.proveedor_service import crear_proveedor

    db = _make_session()
    prov = crear_proveedor(db, ProveedorCreate(codigo="T14-001", nombre="Sin Contacto"))
    assert prov.codigo == "T14-001" and prov.email is None
    db.close()


def test_T14_alta_con_contacto_sqlite():
    from app.services.proveedor_service import crear_proveedor

    db = _make_session()
    prov = crear_proveedor(
        db,
        ProveedorCreate(
            codigo="T14-002",
            nombre="Con Contacto",
            email="a@b.com",
            telefono="+34 600 123 456",
            direccion="Calle 1",
        ),
    )
    assert prov.email == "a@b.com" and prov.telefono == "+34 600 123 456"
    db.close()


def test_T14_duplicado_normalizado_mock_409():
    from app.services.proveedor_service import crear_proveedor

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(
        codigo="T14-003"
    )
    with pytest.raises(HTTPException) as exc:
        crear_proveedor(
            mock_db, ProveedorCreate(codigo="  t14-003 ", nombre="Duplicado")
        )
    assert exc.value.status_code == 409


def test_T14_email_telefono_direccion_null_ausente_vacio():
    """RF-1: null/ausente -> None, '' -> 422."""
    # null y ausente ya probados en alta sin contacto
    # "" debe fallar en schema
    with pytest.raises(Exception):
        ProveedorCreate(codigo="T14-004", nombre="Test", email="")
    with pytest.raises(Exception):
        ProveedorCreate(codigo="T14-005", nombre="Test", telefono="")
    with pytest.raises(Exception):
        ProveedorCreate(codigo="T14-006", nombre="Test", direccion="")


def test_T14_edicion_null_borra_vs_vacio_422():
    """RF-4: null borra, '' -> 422."""
    from app.services.proveedor_service import actualizar_proveedor, crear_proveedor

    db = _make_session()
    crear_proveedor(
        db, ProveedorCreate(codigo="T14-007", nombre="Test", email="old@a.com")
    )
    # null borra
    prov = actualizar_proveedor(db, "T14-007", ProveedorUpdate(email=None))  # type: ignore
    assert prov.email is None
    # "" rechaza en schema
    with pytest.raises(Exception):
        ProveedorUpdate(email="")
    db.close()


def test_T14_edicion_inmutable_400_mock():
    from app.services.proveedor_service import actualizar_proveedor

    mock_db = MagicMock()
    mock_prov = MagicMock(codigo="T14-008", estado="activo")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_prov
    with pytest.raises(HTTPException) as exc:
        actualizar_proveedor(
            mock_db, "T14-008", ProveedorUpdate(nombre="Nuevo", codigo="OTRO-999")
        )  # type: ignore
    assert exc.value.status_code == 400


def test_T14_edicion_inactivo_400():
    from app.services.proveedor_service import actualizar_proveedor

    db = _make_session()
    prov = __import__(
        "app.services.proveedor_service", fromlist=["crear_proveedor"]
    ).crear_proveedor(db, ProveedorCreate(codigo="T14-009", nombre="Test"))
    prov.estado = "inactivo"
    db.commit()
    with pytest.raises(HTTPException) as exc:
        actualizar_proveedor(db, "T14-009", ProveedorUpdate(nombre="Nuevo"))
    assert exc.value.status_code == 400
    db.close()


def test_T14_baja_idempotencia_400():
    from app.services.proveedor_service import baja_proveedor, crear_proveedor

    db = _make_session()
    crear_proveedor(db, ProveedorCreate(codigo="T14-010", nombre="Test"))
    baja_proveedor(db, "T14-010")
    with pytest.raises(HTTPException) as exc:
        baja_proveedor(db, "T14-010")
    assert exc.value.status_code == 400
    db.close()


def test_T14_consultas_filtradas_sqlite():
    from app.services.proveedor_service import (
        crear_proveedor,
        listar_activos,
        obtener_por_codigo,
    )

    db = _make_session()
    crear_proveedor(db, ProveedorCreate(codigo="T14-011", nombre="Activo A"))
    crear_proveedor(db, ProveedorCreate(codigo="T14-012", nombre="Activo B"))
    prov = crear_proveedor(db, ProveedorCreate(codigo="T14-013", nombre="Inactivo"))
    prov.estado = "inactivo"
    db.commit()
    activos = listar_activos(db)
    assert {p.codigo for p in activos} == {"T14-011", "T14-012"}
    # obtener incluye inactivo
    assert obtener_por_codigo(db, "T14-013").estado == "inactivo"
    with pytest.raises(HTTPException) as exc:
        obtener_por_codigo(db, "NOPE")
    assert exc.value.status_code == 404
    db.close()


def test_T14_carrera_integrity_error_mock_409():
    from app.services.proveedor_service import crear_proveedor

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.flush.side_effect = IntegrityError("mock", {}, Exception("unique"))
    mock_db.commit.side_effect = IntegrityError("mock", {}, Exception("unique"))
    with pytest.raises(HTTPException) as exc:
        crear_proveedor(mock_db, ProveedorCreate(codigo="RACE-001", nombre="Race"))
    assert exc.value.status_code == 409
