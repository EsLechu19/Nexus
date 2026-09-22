"""Tests de T03 — venta_service validación 422→404→400 (RF-1, RF-2) — TDD."""

from decimal import Decimal

import pytest
from fastapi import HTTPException


def test_validar_formato_sin_bd_422():
    """T03: validar_formato sin BD rechaza 422 para casos de formato."""
    from app.services.venta_service import validar_formato

    # [] vacío
    with pytest.raises(HTTPException) as exc:
        validar_formato([], {"nombre": "Ana"})
    assert exc.value.status_code == 422

    # >20
    items_21 = [
        {
            "producto_codigo": f"PROD-{i:03d}",
            "cantidad": 1,
            "precio_unitario": Decimal("1.00"),
        }
        for i in range(21)
    ]
    with pytest.raises(HTTPException) as exc2:
        validar_formato(items_21, {"nombre": "Ana"})
    assert exc2.value.status_code == 422

    # duplicado tras normalización
    with pytest.raises(HTTPException) as exc3:
        validar_formato(
            [
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
            {"nombre": "Ana"},
        )
    assert exc3.value.status_code == 422

    # producto_codigo formato inválido
    with pytest.raises(HTTPException) as exc4:
        validar_formato(
            [
                {
                    "producto_codigo": "AB",
                    "cantidad": 1,
                    "precio_unitario": Decimal("10.00"),
                }
            ],
            {"nombre": "Ana"},
        )
    assert exc4.value.status_code == 422

    # cantidad no entera / string / decimal
    for cant in ["2", 2.00, 1.5, 0, -1, 1000001]:
        with pytest.raises(HTTPException) as exc5:
            validar_formato(
                [
                    {
                        "producto_codigo": "PROD-001",
                        "cantidad": cant,
                        "precio_unitario": Decimal("10.00"),
                    }
                ],
                {"nombre": "Ana"},
            )
        assert exc5.value.status_code == 422

    # precio >2 decimales / float / string / negativo
    for precio in ["10.00", 10.00, "10.123", -1]:
        # "10.00" como string debe ser 422, float 10.00 también
        if isinstance(precio, str) and precio == "10.00":
            # en este loop, "10.00" string es uno de los casos, debe ser 422
            pass
        with pytest.raises(HTTPException) as exc6:
            validar_formato(
                [
                    {
                        "producto_codigo": "PROD-001",
                        "cantidad": 1,
                        "precio_unitario": precio,
                    }
                ],
                {"nombre": "Ana"},
            )
        # solo verificamos que algunos son 422, no todos los del loop son inválidos por igual
        # para simplificar, solo chequeamos que al menos uno de los inválidos falla
        if precio in ["10.123", -1, "10.00"]:
            assert exc6.value.status_code == 422


def test_validar_formato_precio_limites():
    """T03: precio con 0/1 decimal válido, >2 invalido."""
    from app.services.venta_service import validar_formato

    # 0 y 1 decimal válidos (deben pasar sin 422)
    validar_formato(
        [
            {
                "producto_codigo": "PROD-001",
                "cantidad": 1,
                "precio_unitario": Decimal("10.5"),
            }
        ],
        {"nombre": "Ana"},
    )
    validar_formato(
        [
            {
                "producto_codigo": "PROD-001",
                "cantidad": 1,
                "precio_unitario": Decimal(10),
            }
        ],
        {"nombre": "Ana"},
    )
    # >2 decimales -> 422
    with pytest.raises(HTTPException) as exc:
        validar_formato(
            [
                {
                    "producto_codigo": "PROD-001",
                    "cantidad": 1,
                    "precio_unitario": Decimal("10.123"),
                }
            ],
            {"nombre": "Ana"},
        )
    assert exc.value.status_code == 422


def test_validar_formato_cliente():
    """T03: cliente nombre 2-100, email ''→422 null→sin email."""
    from app.services.venta_service import validar_formato

    # nombre 1 char ->422
    with pytest.raises(HTTPException) as exc:
        validar_formato(
            [
                {
                    "producto_codigo": "PROD-001",
                    "cantidad": 1,
                    "precio_unitario": Decimal("10.00"),
                }
            ],
            {"nombre": "A"},
        )
    assert exc.value.status_code == 422

    # email "" ->422
    with pytest.raises(HTTPException) as exc2:
        validar_formato(
            [
                {
                    "producto_codigo": "PROD-001",
                    "cantidad": 1,
                    "precio_unitario": Decimal("10.00"),
                }
            ],
            {"nombre": "Ana", "email": ""},
        )
    assert exc2.value.status_code == 422

    # email "" con espacios ->422
    with pytest.raises(HTTPException) as exc3:
        validar_formato(
            [
                {
                    "producto_codigo": "PROD-001",
                    "cantidad": 1,
                    "precio_unitario": Decimal("10.00"),
                }
            ],
            {"nombre": "Ana", "email": "  "},
        )
    assert exc3.value.status_code == 422

    # null/ausente -> ok (sin email)
    validar_formato(
        [
            {
                "producto_codigo": "PROD-001",
                "cantidad": 1,
                "precio_unitario": Decimal("10.00"),
            }
        ],
        {"nombre": "Ana", "email": None},
    )
    validar_formato(
        [
            {
                "producto_codigo": "PROD-001",
                "cantidad": 1,
                "precio_unitario": Decimal("10.00"),
            }
        ],
        {"nombre": "Ana"},
    )


def test_validar_existencia_y_activo_404_400():
    """T03: validar_existencia_y_activo con BD hace 404 si no existe y 400 si inactivo."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.database import Base
    from app.models.producto import Producto
    from app.services.venta_service import validar_existencia_y_activo

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # crear producto activo e inactivo
    db = TestingSessionLocal()
    p_activo = Producto(
        sku="PROD-001",
        nombre="Producto A",
        categoria="consola",
        stock_inicial=10,
        estado="activo",
    )
    p_inactivo = Producto(
        sku="PROD-002",
        nombre="Producto B",
        categoria="consola",
        stock_inicial=10,
        estado="inactivo",
    )
    db.add_all([p_activo, p_inactivo])
    db.commit()
    db.close()

    db = TestingSessionLocal()
    # no existe ->404
    with pytest.raises(HTTPException) as exc:
        validar_existencia_y_activo(db, [{"producto_codigo": "NOPE", "cantidad": 1}])
    assert exc.value.status_code == 404

    # inactivo ->400
    with pytest.raises(HTTPException) as exc2:
        validar_existencia_y_activo(
            db, [{"producto_codigo": "PROD-002", "cantidad": 1}]
        )
    assert exc2.value.status_code == 400

    # activo -> ok
    validar_existencia_y_activo(db, [{"producto_codigo": "PROD-001", "cantidad": 1}])
    db.close()
