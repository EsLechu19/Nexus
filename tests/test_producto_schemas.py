"""Tests de T04 — Schemas Pydantic ProductoCreate / ProductoUpdate / ProductoResponse (RF-1, RF-4)."""

import pytest
from pydantic import ValidationError


def test_producto_create_valido_completo():
    """RF-1: alta válida con todos los campos."""
    from app.schemas.producto import ProductoCreate

    obj = ProductoCreate(
        sku="PS5-SLIM-001",
        nombre="PlayStation 5 Slim",
        categoria="consola",
        stock_inicial=10,
    )
    assert obj.sku == "PS5-SLIM-001"
    assert obj.nombre == "PlayStation 5 Slim"
    assert obj.categoria == "consola"
    assert obj.stock_inicial == 10


def test_producto_create_stock_inicial_opcional_default():
    """RF-1: stock_inicial opcional default 0, admite omitido y null."""
    from app.schemas.producto import ProductoCreate

    obj1 = ProductoCreate(sku="ABC-001", nombre="Juego X", categoria="videojuego")
    assert obj1.stock_inicial == 0

    obj2 = ProductoCreate(
        sku="ABC-002", nombre="Juego Y", categoria="videojuego", stock_inicial=None
    )  # type: ignore
    assert obj2.stock_inicial == 0


def test_producto_create_sku_normalizacion_y_regex():
    """RF-1: sku con espacios debe hacer trim; solo alfanumérico _- y 3-20."""
    from app.schemas.producto import ProductoCreate

    # con espacios internos válidos (trim)
    obj = ProductoCreate(sku="  abc-123_X ", nombre="Test", categoria="accesorio")
    assert obj.sku == "abc-123_X"

    # inválidos
    for sku_invalido in ["AB", "A" * 21, "AB*01", "AB 01", "ABñ01", "", "  "]:
        with pytest.raises(ValidationError):
            ProductoCreate(sku=sku_invalido, nombre="Test", categoria="consola")


def test_producto_create_nombre_trim_y_longitud():
    """RF-1: nombre 2-100 tras trim, no vacío ni solo espacios."""
    from app.schemas.producto import ProductoCreate

    obj = ProductoCreate(sku="SKU-001", nombre="  Zelda  ", categoria="videojuego")
    assert obj.nombre == "Zelda"

    for nombre_invalido in [
        "A",
        "A" * 101,
        "",
        "   ",
        " X ",
    ]:  # último tras trim queda 1 char
        with pytest.raises(ValidationError):
            ProductoCreate(
                sku="SKU-002", nombre=nombre_invalido, categoria="videojuego"
            )


def test_producto_create_categoria_enum_trim_lower():
    """RF-1: categoria enum tras trim+lower; 'juego' y mayúsculas inválidas deben normalizarse o rechazarse."""
    from app.schemas.producto import ProductoCreate

    for cat_ok, esperado in [
        ("consola", "consola"),
        ("  Consola ", "consola"),
        ("VIDEOJUEGO", "videojuego"),
        ("  accesorio ", "accesorio"),
    ]:
        obj = ProductoCreate(sku="SKU-003", nombre="Test", categoria=cat_ok)
        assert obj.categoria == esperado

    for cat_mala in ["juego", "ps5", "", "  ", "video-juego", "consola " * 10]:
        with pytest.raises(ValidationError):
            ProductoCreate(sku="SKU-004", nombre="Test", categoria=cat_mala)


def test_producto_create_stock_inicial_rangos():
    """RF-1: stock_inicial 0-1_000_000, rechaza negativo, decimal, string, >1M."""
    from app.schemas.producto import ProductoCreate

    for ok in [0, 1, 1000000]:
        obj = ProductoCreate(
            sku="SKU-005", nombre="Test", categoria="consola", stock_inicial=ok
        )
        assert obj.stock_inicial == ok

    for malo in [-1, 1000001, 10.5, "10", "abc"]:
        with pytest.raises(ValidationError):
            ProductoCreate(
                sku="SKU-006", nombre="Test", categoria="consola", stock_inicial=malo
            )  # type: ignore


def test_producto_update_valido_parcial():
    """RF-4: ProductoUpdate permite nombre o categoria parcial."""
    from app.schemas.producto import ProductoUpdate

    obj1 = ProductoUpdate(nombre="Nuevo Nombre")
    assert obj1.nombre == "Nuevo Nombre"
    assert obj1.categoria is None

    obj2 = ProductoUpdate(categoria="accesorio")
    assert obj2.categoria == "accesorio"

    obj3 = ProductoUpdate(nombre="  Nuevo  ", categoria="  Consola ")
    assert obj3.nombre == "Nuevo"
    assert obj3.categoria == "consola"


def test_producto_update_exige_al_menos_un_campo():
    """RF-4: ProductoUpdate exige ≥1 campo, rechaza vacío."""
    from app.schemas.producto import ProductoUpdate

    with pytest.raises(ValidationError):
        ProductoUpdate()

    with pytest.raises(ValidationError):
        ProductoUpdate(nombre=None, categoria=None)  # type: ignore


def test_producto_update_valida_longitud_y_enum():
    """RF-4: mismas reglas que Create."""
    from app.schemas.producto import ProductoUpdate

    with pytest.raises(ValidationError):
        ProductoUpdate(nombre="A")
    with pytest.raises(ValidationError):
        ProductoUpdate(categoria="juego")
    with pytest.raises(ValidationError):
        ProductoUpdate(nombre="   ")


def test_producto_response_campos():
    """RF-1..RF-4: ProductoResponse expone sku, nombre, categoria, stock_inicial, estado."""
    from app.schemas.producto import ProductoResponse

    obj = ProductoResponse(
        sku="PS5-001",
        nombre="Test",
        categoria="consola",
        stock_inicial=5,
        estado="activo",
    )
    assert obj.sku == "PS5-001"
    assert obj.estado == "activo"

    # estado debe ser activo/inactivo
    with pytest.raises(ValidationError):
        ProductoResponse(
            sku="PS5-002",
            nombre="Test",
            categoria="consola",
            stock_inicial=0,
            estado="borrado",
        )  # type: ignore
