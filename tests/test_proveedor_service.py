"""Tests de T03 — Service crear_proveedor (RF-1)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.schemas.proveedor import ProveedorCreate


def _make_session():
    from app.models.proveedor import Proveedor  # noqa: F401

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_crear_proveedor_valido_sin_contacto():
    """RF-1: alta sin contacto -> estado activo, nulls."""
    from app.services.proveedor_service import crear_proveedor

    db = _make_session()
    datos = ProveedorCreate(codigo="PROV-001", nombre="Distribuidora Central")
    prov = crear_proveedor(db, datos)
    assert prov.codigo == "PROV-001"
    assert prov.estado == "activo"
    assert prov.email is None and prov.telefono is None and prov.direccion is None
    db.close()


def test_crear_proveedor_valido_con_contacto_completo():
    """RF-1: alta con contacto completo y normalización."""
    from app.services.proveedor_service import crear_proveedor

    db = _make_session()
    datos = ProveedorCreate(
        codigo="  prov-002 ",
        nombre="  Mayorista Norte  ",
        email="  CONTACTO@Central.COM ",
        telefono="+34 912 345 678",
        direccion="Calle Mayor 10",
    )
    prov = crear_proveedor(db, datos)
    assert prov.codigo == "PROV-002"
    assert prov.nombre == "Mayorista Norte"
    assert prov.email == "contacto@central.com"
    assert prov.telefono == "+34 912 345 678"
    assert prov.direccion == "Calle Mayor 10"
    db.close()


def test_crear_proveedor_normaliza_codigo_y_email():
    """RF-1: codigo trim+upper, email trim+lower."""
    from app.services.proveedor_service import crear_proveedor

    db = _make_session()
    datos = ProveedorCreate(codigo="  prov-003 ", nombre="Test", email="  TEST@A.COM ")
    prov = crear_proveedor(db, datos)
    assert prov.codigo == "PROV-003"
    assert prov.email == "test@a.com"
    db.close()


def test_crear_proveedor_rechaza_duplicado_exacto_409():
    """RF-1: código duplicado -> 409."""
    from fastapi import HTTPException

    from app.services.proveedor_service import crear_proveedor

    db = _make_session()
    crear_proveedor(db, ProveedorCreate(codigo="DUPL-001", nombre="A Valid Name"))
    with pytest.raises(HTTPException) as exc:
        crear_proveedor(db, ProveedorCreate(codigo="DUPL-001", nombre="Otro Nombre"))
    assert exc.value.status_code == 409
    db.close()


def test_crear_proveedor_rechaza_duplicado_normalizado_409():
    """RF-1: duplicado normalizado -> 409."""
    from fastapi import HTTPException

    from app.services.proveedor_service import crear_proveedor

    db = _make_session()
    crear_proveedor(db, ProveedorCreate(codigo="PROV-004", nombre="Proveedor A"))
    with pytest.raises(HTTPException) as exc:
        crear_proveedor(db, ProveedorCreate(codigo="  prov-004 ", nombre="Proveedor B"))
    assert exc.value.status_code == 409
    db.close()


def test_crear_proveedor_rechaza_duplicado_inactivo_409():
    """RNF-3: código de inactivo no reutilizable -> 409."""
    from fastapi import HTTPException

    from app.services.proveedor_service import crear_proveedor

    db = _make_session()
    prov = crear_proveedor(
        db, ProveedorCreate(codigo="INACT-001", nombre="Proveedor Inactivo")
    )
    prov.estado = "inactivo"
    db.commit()
    with pytest.raises(HTTPException) as exc:
        crear_proveedor(
            db, ProveedorCreate(codigo="INACT-001", nombre="Nuevo Proveedor")
        )
    assert exc.value.status_code == 409
    db.close()


def test_crear_proveedor_captura_integrity_error_409():
    """RF-1: carrera IntegrityError -> 409."""
    from unittest.mock import MagicMock

    from fastapi import HTTPException
    from sqlalchemy.exc import IntegrityError

    from app.services.proveedor_service import crear_proveedor

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.commit.side_effect = IntegrityError("mock", {}, Exception("unique"))
    mock_db.flush.side_effect = IntegrityError("mock", {}, Exception("unique"))
    datos = ProveedorCreate(codigo="RACE-001", nombre="Race Proveedor")
    with pytest.raises(HTTPException) as exc:
        crear_proveedor(mock_db, datos)
    assert exc.value.status_code == 409
