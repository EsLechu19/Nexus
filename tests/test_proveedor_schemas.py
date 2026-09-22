"""Tests de T02 — Schemas Pydantic ProveedorCreate / ProveedorUpdate / ProveedorResponse (RF-1, RF-4)."""

import pytest
from pydantic import ValidationError


def test_proveedor_create_valido_completo():
    """RF-1: alta válida con todos los campos."""
    from app.schemas.proveedor import ProveedorCreate

    obj = ProveedorCreate(
        codigo="PROV-001",
        nombre="Distribuidora Central",
        email="contacto@central.com",
        telefono="+34 912 345 678",
        direccion="Calle Mayor 10, Madrid",
    )
    assert obj.codigo == "PROV-001"
    assert obj.email == "contacto@central.com"
    assert obj.telefono == "+34 912 345 678"
    assert obj.direccion == "Calle Mayor 10, Madrid"


def test_proveedor_create_sin_contacto():
    """RF-1: contacto opcional -> None si omitido o null."""
    from app.schemas.proveedor import ProveedorCreate

    obj1 = ProveedorCreate(codigo="PROV-002", nombre="Mayorista Norte")
    assert obj1.email is None and obj1.telefono is None and obj1.direccion is None

    obj2 = ProveedorCreate(
        codigo="PROV-003", nombre="Test", email=None, telefono=None, direccion=None
    )  # type: ignore
    assert obj2.email is None


def test_proveedor_create_codigo_normalizacion_y_regex():
    """RF-1: codigo trim y 3-20 alfanumérico _-."""
    from app.schemas.proveedor import ProveedorCreate

    obj = ProveedorCreate(codigo="  prov-001 ", nombre="Test")
    assert obj.codigo == "PROV-001"

    for invalido in ["AB", "A" * 21, "AB*01", "AB 01", "ABñ01", "", "  "]:
        with pytest.raises(ValidationError):
            ProveedorCreate(codigo=invalido, nombre="Test")


def test_proveedor_create_nombre_trim_y_longitud():
    """RF-1: nombre 2-100 tras trim."""
    from app.schemas.proveedor import ProveedorCreate

    obj = ProveedorCreate(codigo="PROV-004", nombre="  Distribuidora  ")
    assert obj.nombre == "Distribuidora"

    for invalido in ["A", "A" * 101, "", "   ", " X "]:
        with pytest.raises(ValidationError):
            ProveedorCreate(codigo="PROV-005", nombre=invalido)


def test_proveedor_create_email_formato_y_normalizacion():
    """RF-1: email trim+lower, formato válido, "" -> 422, null -> None."""
    from app.schemas.proveedor import ProveedorCreate

    obj = ProveedorCreate(
        codigo="PROV-006", nombre="Test", email="  CONTACTO@Central.COM "
    )
    assert obj.email == "contacto@central.com"

    for invalido in [
        "sinarroba",
        "test@",
        "test@.com",
        "test@dom",
        "test @dom.com",
        "",
        "A" * 255 + "@a.com",
    ]:
        with pytest.raises(ValidationError):
            ProveedorCreate(codigo="PROV-007", nombre="Test", email=invalido)

    # null y ausente aceptados
    obj2 = ProveedorCreate(codigo="PROV-008", nombre="Test", email=None)  # type: ignore
    assert obj2.email is None


def test_proveedor_create_telefono_formato():
    """RF-1: telefono 7-15 dígitos, + solo inicio, espacios/guiones/() permitidos."""
    from app.schemas.proveedor import ProveedorCreate

    for valido in ["+34 912 345 678", "912345678", "+1 (555) 123-4567", "600 123 456"]:
        obj = ProveedorCreate(codigo="PROV-009", nombre="Test", telefono=valido)
        assert obj.telefono == valido.strip()

    for invalido in [
        "123456",
        "1" * 16,
        "abc123456",
        "12+34 567",
        "123-abc-456",
        "",
        "++34 123",
        "123456+789",
    ]:
        with pytest.raises(ValidationError):
            ProveedorCreate(codigo="PROV-010", nombre="Test", telefono=invalido)


def test_proveedor_create_direccion_longitud():
    """RF-1: direccion 5-200 tras trim, "" -> 422, null -> None."""
    from app.schemas.proveedor import ProveedorCreate

    obj = ProveedorCreate(codigo="PROV-011", nombre="Test", direccion="Calle Mayor 10")
    assert obj.direccion == "Calle Mayor 10"

    for invalido in ["abcd", "A" * 201, "", "   ", "a\nb"]:
        with pytest.raises(ValidationError):
            ProveedorCreate(codigo="PROV-012", nombre="Test", direccion=invalido)

    obj2 = ProveedorCreate(codigo="PROV-013", nombre="Test", direccion=None)  # type: ignore
    assert obj2.direccion is None


def test_proveedor_update_valido_parcial_y_borrado_null():
    """RF-4: update permite parcial, null borra, exige ≥1 campo."""
    from app.schemas.proveedor import ProveedorUpdate

    obj1 = ProveedorUpdate(nombre="Nuevo Nombre")
    assert obj1.nombre == "Nuevo Nombre"

    obj2 = ProveedorUpdate(email="nuevo@central.com")
    assert obj2.email == "nuevo@central.com"

    obj3 = ProveedorUpdate(email=None)  # type: ignore
    assert obj3.email is None  # borra

    obj4 = ProveedorUpdate(nombre="  Nuevo  ", email="  TEST@a.com ")
    assert obj4.nombre == "Nuevo"
    assert obj4.email == "test@a.com"


def test_proveedor_update_exige_al_menos_un_campo():
    """RF-4: payload vacío sin nombre/email/telefono/direccion -> 422."""
    from app.schemas.proveedor import ProveedorUpdate

    with pytest.raises(ValidationError):
        ProveedorUpdate()

    with pytest.raises(ValidationError):
        ProveedorUpdate(codigo="PROV-001")  # type: ignore # solo codigo no cuenta


def test_proveedor_update_validaciones_y_codigo_inmutable():
    """RF-4: validaciones y codigo inmutable."""
    from app.schemas.proveedor import ProveedorUpdate

    with pytest.raises(ValidationError):
        ProveedorUpdate(nombre="A")
    with pytest.raises(ValidationError):
        ProveedorUpdate(email="sinarroba")
    with pytest.raises(ValidationError):
        ProveedorUpdate(telefono="123")
    with pytest.raises(ValidationError):
        ProveedorUpdate(direccion="ab")
    # codigo con formato válido pero se permite (para inmutabilidad en service)
    obj = ProveedorUpdate(nombre="Valido", codigo="PROV-001")  # type: ignore
    assert obj.codigo == "PROV-001"


def test_proveedor_response_campos():
    """RF-1..RF-5: ProveedorResponse con codigo, nombre, contacto, estado."""
    from app.schemas.proveedor import ProveedorResponse

    obj = ProveedorResponse(
        codigo="PROV-001",
        nombre="Test",
        email="a@b.com",
        telefono="+34 123",
        direccion="Dir",
        estado="activo",
    )
    assert obj.codigo == "PROV-001"
    assert obj.estado == "activo"

    with pytest.raises(ValidationError):
        ProveedorResponse(
            codigo="PROV-002",
            nombre="Test",
            email="a@b.com",
            telefono="123",
            direccion="Dir",
            estado="borrado",
        )  # type: ignore


def test_proveedor_list_response_sin_estado():
    """RF-2: listado sin estado."""
    from app.schemas.proveedor import ProveedorListResponse

    obj = ProveedorListResponse(
        codigo="PROV-001", nombre="Test", email=None, telefono=None, direccion=None
    )
    assert obj.codigo == "PROV-001"
    assert not hasattr(obj, "estado") or obj.model_fields.get("estado") is None
