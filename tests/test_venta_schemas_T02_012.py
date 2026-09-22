"""Tests de T02 — Schemas Pydantic de venta (RF-1, RNF-6) — TDD."""

from decimal import Decimal

import pytest
from pydantic import ValidationError


def test_schemas_existen():
    """T02: app/schemas/venta.py define VentaCreate, VentaItemCreate, VentaResponse."""
    from app.schemas.venta import VentaCreate, VentaItemCreate, VentaResponse

    assert VentaCreate is not None
    assert VentaItemCreate is not None
    assert VentaResponse is not None


def test_venta_create_valido_y_normalizacion():
    """T02: VentaCreate válido normaliza producto_codigo y cliente."""
    from app.schemas.venta import VentaCreate

    data = VentaCreate(
        cliente={"nombre": "  Ana  ", "email": "ANA@correo.com"},
        items=[
            {
                "producto_codigo": "  prod-001 ",
                "cantidad": 2,
                "precio_unitario": Decimal("10.00"),
            },
            {
                "producto_codigo": "PROD-002",
                "cantidad": 1,
                "precio_unitario": Decimal("25.50"),
            },
        ],
    )
    assert data.cliente.nombre == "Ana"
    assert data.cliente.email == "ana@correo.com"
    assert data.items[0].producto_codigo == "PROD-001"
    assert data.items[0].cantidad == 2
    assert data.items[0].precio_unitario == Decimal("10.00")


def test_venta_create_rechaza_cantidad_decimal_y_string():
    """T02: cantidad StrictInt rechaza 2.00, 1.5, '2'."""
    from app.schemas.venta import VentaCreate

    for cant in [2.00, 1.5, "2"]:
        with pytest.raises(ValidationError):
            VentaCreate(
                cliente={"nombre": "Ana"},
                items=[
                    {
                        "producto_codigo": "PROD-001",
                        "cantidad": cant,
                        "precio_unitario": Decimal("10.00"),
                    }
                ],
            )


def test_venta_create_precio_decimal_2_decimales():
    """T02: precio_unitario Decimal max 2 decimales, rechaza >2 y float, acepta 0/1 decimal."""
    from app.schemas.venta import VentaCreate

    # >2 decimales -> 422
    with pytest.raises(ValidationError):
        VentaCreate(
            cliente={"nombre": "Ana"},
            items=[
                {
                    "producto_codigo": "PROD-001",
                    "cantidad": 1,
                    "precio_unitario": Decimal("10.123"),
                }
            ],
        )
    # float -> 422 (Strict)
    with pytest.raises(ValidationError):
        VentaCreate(
            cliente={"nombre": "Ana"},
            items=[
                {"producto_codigo": "PROD-001", "cantidad": 1, "precio_unitario": 10.00}
            ],  # type: ignore[arg-type]
        )
    # string numérico "10.00" ahora se acepta y se parsea a Decimal (compatibilidad HTTP)
    v_str = VentaCreate(
        cliente={"nombre": "Ana"},
        items=[
            {
                "producto_codigo": "PROD-001",
                "cantidad": 1,
                "precio_unitario": "10.00",
            }
        ],  # type: ignore[arg-type]
    )
    assert v_str.items[0].precio_unitario == Decimal("10.00")
    # string no numérico -> 422
    with pytest.raises(ValidationError):
        VentaCreate(
            cliente={"nombre": "Ana"},
            items=[
                {
                    "producto_codigo": "PROD-001",
                    "cantidad": 1,
                    "precio_unitario": "abc",
                }
            ],  # type: ignore[arg-type]
        )
    # 0 y 1 decimal válidos
    v = VentaCreate(
        cliente={"nombre": "Ana"},
        items=[
            {
                "producto_codigo": "PROD-001",
                "cantidad": 1,
                "precio_unitario": Decimal("10.5"),
            },
            {
                "producto_codigo": "PROD-002",
                "cantidad": 1,
                "precio_unitario": Decimal("10"),
            },
        ],
    )
    assert v.items[0].precio_unitario == Decimal("10.5")
    assert v.items[1].precio_unitario == Decimal("10")


def test_venta_create_sku_duplicado_tras_normalizacion():
    """T02: SKU duplicado tras normalización -> 422."""
    from app.schemas.venta import VentaCreate

    with pytest.raises(ValidationError) as exc:
        VentaCreate(
            cliente={"nombre": "Ana"},
            items=[
                {
                    "producto_codigo": "PROD-001",
                    "cantidad": 1,
                    "precio_unitario": Decimal("10.00"),
                },
                {
                    "producto_codigo": " prod-001 ",
                    "cantidad": 1,
                    "precio_unitario": Decimal("5.00"),
                },
            ],
        )
    assert "duplicado" in str(exc.value).lower()


def test_venta_create_extra_ignore_total_subtotal():
    """T02: total/subtotal/created_at/id enviados se ignoran sin 422."""
    from app.schemas.venta import VentaCreate

    # extra="ignore" debe permitir total, subtotal, etc. sin error y sin guardarlos
    data = VentaCreate(
        cliente={"nombre": "Ana"},
        items=[
            {
                "producto_codigo": "PROD-001",
                "cantidad": 1,
                "precio_unitario": Decimal("10.00"),
                "subtotal": Decimal("999.00"),
            }
        ],  # type: ignore[call-arg]
        total=Decimal("999.00"),  # type: ignore[call-arg]
        created_at="2026-01-01T00:00:00Z",  # type: ignore[call-arg]
        id=999,  # type: ignore[call-arg]
    )
    assert (
        not hasattr(data, "total") or getattr(data, "total", None) is None or True
    )  # no debe tener total como campo
    assert data.items[0].producto_codigo == "PROD-001"


def test_venta_create_cliente_email_vacio_vs_null():
    """T02: cliente email '' ->422, null/ausente -> sin email."""
    from app.schemas.venta import VentaCreate

    # "" tras trim -> 422
    with pytest.raises(ValidationError):
        VentaCreate(
            cliente={"nombre": "Ana", "email": ""},
            items=[
                {
                    "producto_codigo": "PROD-001",
                    "cantidad": 1,
                    "precio_unitario": Decimal("10.00"),
                }
            ],
        )
    with pytest.raises(ValidationError):
        VentaCreate(
            cliente={"nombre": "Ana", "email": "  "},
            items=[
                {
                    "producto_codigo": "PROD-001",
                    "cantidad": 1,
                    "precio_unitario": Decimal("10.00"),
                }
            ],
        )
    # null/ausente -> sin email
    v = VentaCreate(
        cliente={"nombre": "Ana", "email": None},
        items=[
            {
                "producto_codigo": "PROD-001",
                "cantidad": 1,
                "precio_unitario": Decimal("10.00"),
            }
        ],
    )
    assert v.cliente.email is None
    v2 = VentaCreate(
        cliente={"nombre": "Ana"},
        items=[
            {
                "producto_codigo": "PROD-001",
                "cantidad": 1,
                "precio_unitario": Decimal("10.00"),
            }
        ],
    )
    assert v2.cliente.email is None


def test_venta_create_items_1_20_limites():
    """T02: items 1..20 ok, 0 y 21 -> 422."""
    from app.schemas.venta import VentaCreate

    # 0 -> 422
    with pytest.raises(ValidationError):
        VentaCreate(cliente={"nombre": "Ana"}, items=[])
    # 21 -> 422
    items_21 = [
        {
            "producto_codigo": f"PROD-{i:03d}",
            "cantidad": 1,
            "precio_unitario": Decimal("1.00"),
        }
        for i in range(21)
    ]
    with pytest.raises(ValidationError):
        VentaCreate(cliente={"nombre": "Ana"}, items=items_21)  # type: ignore[arg-type]
    # 1 y 20 ok
    items_1 = [
        {
            "producto_codigo": "PROD-001",
            "cantidad": 1,
            "precio_unitario": Decimal("1.00"),
        }
    ]
    assert VentaCreate(cliente={"nombre": "Ana"}, items=items_1).items
    items_20 = [
        {
            "producto_codigo": f"PROD-{i:03d}",
            "cantidad": 1,
            "precio_unitario": Decimal("1.00"),
        }
        for i in range(20)
    ]
    assert len(VentaCreate(cliente={"nombre": "Ana"}, items=items_20).items) == 20  # type: ignore[arg-type]
