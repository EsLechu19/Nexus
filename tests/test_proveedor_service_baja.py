"""Tests de T06 — Service baja_proveedor (RF-5)."""

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


def _crear(
    db,
    codigo="PROV-001",
    nombre="Proveedor Test",
    email=None,
    telefono=None,
    direccion=None,
):
    from app.services.proveedor_service import crear_proveedor

    return crear_proveedor(
        db,
        ProveedorCreate(
            codigo=codigo,
            nombre=nombre,
            email=email,
            telefono=telefono,
            direccion=direccion,
        ),
    )


def test_baja_proveedor_activo_a_inactivo():
    """RF-5: marca activo -> inactivo."""
    from app.services.proveedor_service import baja_proveedor

    db = _make_session()
    _crear(db, codigo="BAJA-001")
    prov = baja_proveedor(db, "BAJA-001")
    assert prov.estado == "inactivo"
    assert prov.codigo == "BAJA-001"
    db.close()


def test_baja_proveedor_con_contacto_permite():
    """RF-5: permite baja con cualquier contacto."""
    from app.services.proveedor_service import baja_proveedor

    db = _make_session()
    _crear(
        db,
        codigo="BAJA-002",
        email="a@b.com",
        telefono="+34 123 456 789",
        direccion="Calle 1",
    )
    prov = baja_proveedor(db, "BAJA-002")
    assert prov.estado == "inactivo"
    db.close()


def test_baja_proveedor_ya_inactivo_400():
    """RF-5: ya inactivo -> 400, no idempotente."""
    from fastapi import HTTPException
    from app.services.proveedor_service import baja_proveedor

    db = _make_session()
    _crear(db, codigo="BAJA-003")
    baja_proveedor(db, "BAJA-003")
    with pytest.raises(HTTPException) as exc:
        baja_proveedor(db, "BAJA-003")
    assert exc.value.status_code == 400
    db.close()


def test_baja_proveedor_no_encontrado_404():
    """RF-5: código inexistente -> 404."""
    from fastapi import HTTPException
    from app.services.proveedor_service import baja_proveedor

    db = _make_session()
    with pytest.raises(HTTPException) as exc:
        baja_proveedor(db, "NO-EXISTE")
    assert exc.value.status_code == 404
    db.close()


def test_baja_proveedor_normaliza_codigo_path():
    """RF-5: código path normalizado trim+upper."""
    from app.services.proveedor_service import baja_proveedor

    db = _make_session()
    _crear(db, codigo="BAJA-004")
    prov = baja_proveedor(db, "  baja-004 ")
    assert prov.estado == "inactivo"
    db.close()


def test_baja_proveedor_no_borra_y_excluido_de_listado():
    """RF-5 y RNF-1: no borra, excluido de listado pero visible en detalle."""
    from app.services.proveedor_service import (
        baja_proveedor,
        listar_activos,
        obtener_por_codigo,
    )
    from app.models.proveedor import Proveedor

    db = _make_session()
    _crear(db, codigo="BAJA-005", nombre="Visible")
    _crear(db, codigo="BAJA-006", nombre="Otro")
    baja_proveedor(db, "BAJA-005")

    assert (
        db.query(Proveedor).filter(Proveedor.codigo == "BAJA-005").first() is not None
    )
    activos = listar_activos(db)
    assert {p.codigo for p in activos} == {"BAJA-006"}
    prod = obtener_por_codigo(db, "BAJA-005")
    assert prod.estado == "inactivo"
    db.close()
