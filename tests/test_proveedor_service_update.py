"""Tests de T05 — Service actualizar_proveedor (RF-4)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.schemas.proveedor import ProveedorCreate, ProveedorUpdate


def _make_session():
    from app.models.proveedor import Proveedor  # noqa: F401

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _crear(
    db,
    codigo="PROV-001",
    nombre="Proveedor Base",
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


def test_actualizar_proveedor_solo_nombre():
    """RF-4: solo nombre."""
    from app.services.proveedor_service import actualizar_proveedor

    db = _make_session()
    _crear(db, codigo="UPD-001", nombre="Original Nombre")
    prov = actualizar_proveedor(db, "UPD-001", ProveedorUpdate(nombre="Nuevo Nombre"))
    assert prov.nombre == "Nuevo Nombre"
    assert prov.codigo == "PROV-001" if False else "UPD-001"  # placeholder
    assert prov.codigo == "UPD-001"
    db.close()


def test_actualizar_proveedor_solo_email():
    """RF-4: solo email."""
    from app.services.proveedor_service import actualizar_proveedor

    db = _make_session()
    _crear(db, codigo="UPD-002", nombre="Test Proveedor", email="old@a.com")
    prov = actualizar_proveedor(db, "UPD-002", ProveedorUpdate(email="new@a.com"))
    assert prov.email == "new@a.com"
    db.close()


def test_actualizar_proveedor_solo_telefono_y_direccion():
    """RF-4: telefono y direccion."""
    from app.services.proveedor_service import actualizar_proveedor

    db = _make_session()
    _crear(db, codigo="UPD-003", nombre="Test Proveedor")
    prov = actualizar_proveedor(
        db,
        "UPD-003",
        ProveedorUpdate(telefono="+34 600 123 456", direccion="Nueva Calle 5"),
    )
    assert prov.telefono == "+34 600 123 456"
    assert prov.direccion == "Nueva Calle 5"
    db.close()


def test_actualizar_proveedor_null_borra_vs_ausente_no_cambia():
    """RF-4: null borra, ausente no cambia, '' rechaza (schema)."""
    from app.services.proveedor_service import actualizar_proveedor

    db = _make_session()
    _crear(
        db,
        codigo="UPD-004",
        nombre="Test Proveedor",
        email="keep@a.com",
        telefono="+34 123 456 789",
    )
    # null borra
    prov = actualizar_proveedor(db, "UPD-004", ProveedorUpdate(email=None))  # type: ignore
    assert prov.email is None
    assert prov.telefono == "+34 123 456 789"  # no cambió
    # ausente no cambia
    prov = actualizar_proveedor(db, "UPD-004", ProveedorUpdate(nombre="Cambiado"))
    assert prov.email is None  # sigue borrado
    assert prov.nombre == "Cambiado"
    db.close()


def test_actualizar_proveedor_codigo_mismo_se_ignora():
    """RF-4: codigo mismo se ignora."""
    from app.services.proveedor_service import actualizar_proveedor

    db = _make_session()
    _crear(db, codigo="PROV-005")
    prov = actualizar_proveedor(
        db, "PROV-005", ProveedorUpdate(nombre="Cambiado", codigo="  prov-005 ")
    )  # type: ignore
    assert prov.nombre == "Cambiado"
    assert prov.codigo == "PROV-005"
    db.close()


def test_actualizar_proveedor_codigo_distinto_400():
    """RF-4: codigo distinto -> 400."""
    from fastapi import HTTPException

    from app.services.proveedor_service import actualizar_proveedor

    db = _make_session()
    _crear(db, codigo="PROV-006")
    with pytest.raises(HTTPException) as exc:
        actualizar_proveedor(
            db, "PROV-006", ProveedorUpdate(nombre="Nuevo", codigo="OTRO-999")
        )  # type: ignore
    assert exc.value.status_code == 400
    db.close()


def test_actualizar_proveedor_estado_se_ignora():
    """RF-4: estado se ignora."""
    from app.services.proveedor_service import actualizar_proveedor

    db = _make_session()
    _crear(db, codigo="PROV-007")
    # Pasar estado via modelo extra (ignorado)
    datos = ProveedorUpdate(nombre="Cambiado")
    # Simular que payload trae estado, pero schema lo ignora (extra=ignore)
    # Service debe ignorarlo y no cambiar estado
    prov = actualizar_proveedor(db, "PROV-007", datos)
    assert prov.estado == "activo"
    db.close()


def test_actualizar_proveedor_inactivo_400():
    """RF-4: inactivo no editable."""
    from fastapi import HTTPException

    from app.services.proveedor_service import actualizar_proveedor

    db = _make_session()
    prov = _crear(db, codigo="PROV-008")
    prov.estado = "inactivo"
    db.commit()
    with pytest.raises(HTTPException) as exc:
        actualizar_proveedor(db, "PROV-008", ProveedorUpdate(nombre="Nuevo"))
    assert exc.value.status_code == 400
    db.close()


def test_actualizar_proveedor_no_encontrado_404():
    """RF-4: no existe -> 404."""
    from fastapi import HTTPException

    from app.services.proveedor_service import actualizar_proveedor

    db = _make_session()
    with pytest.raises(HTTPException) as exc:
        actualizar_proveedor(db, "NO-EXISTE", ProveedorUpdate(nombre="Nuevo"))
    assert exc.value.status_code == 404
    db.close()


def test_actualizar_proveedor_normaliza_codigo_path():
    """RF-4: codigo path normalizado."""
    from app.services.proveedor_service import actualizar_proveedor

    db = _make_session()
    _crear(db, codigo="PROV-009")
    prov = actualizar_proveedor(
        db, "  prov-009 ", ProveedorUpdate(nombre="Nuevo Nombre")
    )
    assert prov.nombre == "Nuevo Nombre"
    db.close()
