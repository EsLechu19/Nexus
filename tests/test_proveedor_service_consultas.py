"""Tests de T04 — Service listar_activos y obtener_por_codigo (RF-2, RF-3)."""

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


def test_listar_activos_vacio():
    """RF-2: sin proveedores -> []"""
    from app.services.proveedor_service import listar_activos

    db = _make_session()
    assert listar_activos(db) == []
    db.close()


def test_listar_activos_solo_activos_ordenados():
    """RF-2: solo activos ordenados por codigo, con email/telefono/direccion sin estado."""
    from app.services.proveedor_service import listar_activos

    db = _make_session()
    _crear(db, codigo="PROV-002", nombre="Proveedor B", email="b@a.com")
    _crear(db, codigo="PROV-001", nombre="Proveedor A")
    prov_inactivo = _crear(db, codigo="PROV-003", nombre="Proveedor C")
    prov_inactivo.estado = "inactivo"
    db.commit()

    activos = listar_activos(db)
    assert [p.codigo for p in activos] == ["PROV-001", "PROV-002"]
    for p in activos:
        assert p.estado == "activo"
        assert hasattr(p, "codigo") and hasattr(p, "nombre")
    # Sin estado en listado no se expone, pero service devuelve modelo con estado; router lo filtrará
    db.close()


def test_obtener_por_codigo_activo_detalle():
    """RF-3: detalle activo incluye estado."""
    from app.services.proveedor_service import obtener_por_codigo

    db = _make_session()
    _crear(
        db,
        codigo="PROV-010",
        nombre="Central Distribuidora",
        email="a@b.com",
        telefono="+34 912 345 678",
        direccion="Calle Mayor 10",
    )
    prod = obtener_por_codigo(db, "PROV-010")
    assert prod.codigo == "PROV-010"
    assert prod.nombre == "Central Distribuidora"
    assert prod.estado == "activo"
    assert prod.email == "a@b.com"
    db.close()


def test_obtener_por_codigo_inactivo_trazabilidad():
    """RF-3: detalle inactivo también accesible."""
    from app.services.proveedor_service import obtener_por_codigo

    db = _make_session()
    prov = _crear(db, codigo="PROV-011", nombre="Baja")
    prov.estado = "inactivo"
    db.commit()
    fetched = obtener_por_codigo(db, "PROV-011")
    assert fetched.estado == "inactivo"
    db.close()


def test_obtener_por_codigo_normalizado():
    """RF-3: normaliza trim+upper."""
    from app.services.proveedor_service import obtener_por_codigo

    db = _make_session()
    _crear(db, codigo="PROV-012", nombre="Test")
    prod = obtener_por_codigo(db, "  prov-012 ")
    assert prod.codigo == "PROV-012"
    db.close()


def test_obtener_por_codigo_no_existe_404():
    """RF-3: no existe -> 404."""
    from fastapi import HTTPException
    from app.services.proveedor_service import obtener_por_codigo

    db = _make_session()
    with pytest.raises(HTTPException) as exc:
        obtener_por_codigo(db, "NO-EXISTE")
    assert exc.value.status_code == 404
    assert "no encontrado" in exc.value.detail.lower()
    db.close()
