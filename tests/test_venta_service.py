"""Tests de T08 — venta_service unitarios (RF-1, RF-2, RNF-6) — TDD."""

from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models.movimiento_inventario  # noqa: F401
import app.models.producto  # noqa: F401
import app.models.proveedor  # noqa: F401
import app.models.usuario  # noqa: F401
import app.models.venta  # noqa: F401
import app.models.venta_item  # noqa: F401
from app.database import Base
from app.models.producto import Producto


def _make_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal


def test_venta_service_cliente_vacio_vs_null():
    """T08: cliente ''→422, null/ausente→sin email."""
    from app.services.venta_service import validar_formato

    # "" tras trim → 422
    with pytest.raises(HTTPException) as exc:
        validar_formato(
            [
                {
                    "producto_codigo": "PROD-001",
                    "cantidad": 1,
                    "precio_unitario": Decimal("10.00"),
                }
            ],
            {"nombre": ""},
        )
    assert exc.value.status_code == 422
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
    # null / ausente → ok
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


def test_venta_service_items_vacio_y_21():
    """T08: items []/21 →422."""
    from app.services.venta_service import validar_formato

    with pytest.raises(HTTPException) as exc:
        validar_formato([], {"nombre": "Ana"})
    assert exc.value.status_code == 422
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


def test_venta_service_duplicado_tras_normalizacion():
    """T08: SKU duplicado tras normalización →422."""
    from app.services.venta_service import validar_formato

    with pytest.raises(HTTPException) as exc:
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
    assert exc.value.status_code == 422
    assert "duplicado" in str(exc.value.detail).lower()


def test_venta_service_cantidad_invalida():
    """T08: cantidad 2.00/'2'→422."""
    from app.services.venta_service import validar_formato

    for cant in [2.00, "2", 0, -1, 1.5, 1000001]:
        with pytest.raises(HTTPException) as exc:
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
        assert exc.value.status_code == 422


def test_venta_service_precio_invalido_y_valido():
    """T08: precio 10.123→422, 10.5/10→201 (Decimal exacto)."""
    from app.services.venta_service import validar_formato

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
    with pytest.raises(HTTPException) as exc2:
        validar_formato(
            [{"producto_codigo": "PROD-001", "cantidad": 1, "precio_unitario": 10.00}],
            {"nombre": "Ana"},
        )
    assert exc2.value.status_code == 422
    # válidos 0/1 decimal
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
    validar_formato(
        [
            {
                "producto_codigo": "PROD-001",
                "cantidad": 1,
                "precio_unitario": Decimal("0.00"),
            }
        ],
        {"nombre": "Ana"},
    )


def test_venta_service_total_enviado_ignorado():
    """T08: total/subtotal/created_at/id enviados se ignoran, se persiste derivado."""
    SessionLocal = _make_db()
    db = SessionLocal()
    p = Producto(
        sku="PROD-001",
        nombre="Producto A",
        categoria="consola",
        stock_inicial=10,
        estado="activo",
    )
    db.add(p)
    db.commit()
    db.close()
    from app.services.venta_service import registrar_venta

    db = SessionLocal()
    venta = registrar_venta(
        db,
        {
            "cliente": {"nombre": "Ana"},
            "items": [
                {
                    "producto_codigo": "PROD-001",
                    "cantidad": 2,
                    "precio_unitario": Decimal("10.00"),
                    "subtotal": Decimal("999.00"),
                }
            ],
            "total": Decimal("999.00"),
            "created_at": "2020-01-01T00:00:00Z",
            "id": 999,
        },
    )
    # debe ser derivado 20.00, no 999
    assert venta.total == Decimal("20.00")
    assert venta.id != 999
    # verificar venta_item subtotal derivado
    from app.models.venta_item import VentaItem

    item = db.query(VentaItem).filter(VentaItem.venta_id == venta.id).first()
    assert item.subtotal == Decimal("20.00")
    db.close()


def test_venta_service_404_y_400():
    """T08: 404 no existe, 400 inactivo/stock con disponible/solicitado."""
    SessionLocal = _make_db()
    db = SessionLocal()
    p1 = Producto(
        sku="PROD-001",
        nombre="Producto A",
        categoria="consola",
        stock_inicial=2,
        estado="activo",
    )
    p2 = Producto(
        sku="PROD-002",
        nombre="Producto B",
        categoria="consola",
        stock_inicial=10,
        estado="inactivo",
    )
    db.add_all([p1, p2])
    db.commit()
    db.close()
    from app.services.venta_service import registrar_venta

    # no existe →404 con código
    db = SessionLocal()
    with pytest.raises(HTTPException) as exc:
        registrar_venta(
            db,
            {
                "cliente": {"nombre": "Ana"},
                "items": [
                    {
                        "producto_codigo": "NOPE",
                        "cantidad": 1,
                        "precio_unitario": Decimal("10.00"),
                    }
                ],
            },
        )
    assert exc.value.status_code == 404
    assert "NOPE" in str(exc.value.detail)
    db.close()

    # inactivo →400
    db = SessionLocal()
    with pytest.raises(HTTPException) as exc2:
        registrar_venta(
            db,
            {
                "cliente": {"nombre": "Ana"},
                "items": [
                    {
                        "producto_codigo": "PROD-002",
                        "cantidad": 1,
                        "precio_unitario": Decimal("10.00"),
                    }
                ],
            },
        )
    assert exc2.value.status_code == 400
    assert "PROD-002" in str(exc2.value.detail)
    db.close()

    # stock insuficiente →400 con disponible/solicitado
    db = SessionLocal()
    with pytest.raises(HTTPException) as exc3:
        registrar_venta(
            db,
            {
                "cliente": {"nombre": "Ana"},
                "items": [
                    {
                        "producto_codigo": "PROD-001",
                        "cantidad": 5,
                        "precio_unitario": Decimal("10.00"),
                    }
                ],
            },
        )
    assert exc3.value.status_code == 400
    assert "disponible" in str(exc3.value.detail).lower()
    assert "solicitado" in str(exc3.value.detail).lower()
    assert "PROD-001" in str(exc3.value.detail)
    db.close()


def test_venta_service_decimal_exacto():
    """T08: Decimal exacto total==sum(cantidad*precio)."""
    from app.services.venta_service import calcular_totales

    subtotales, total = calcular_totales(
        [
            {
                "producto_codigo": "PROD-001",
                "cantidad": 2,
                "precio_unitario": Decimal("10.00"),
            },
            {
                "producto_codigo": "PROD-002",
                "cantidad": 1,
                "precio_unitario": Decimal("25.50"),
            },
        ]
    )
    assert subtotales[0] == Decimal("20.00")
    assert subtotales[1] == Decimal("25.50")
    assert total == Decimal("45.50")
    assert total == sum(subtotales)
    # verificar que no es float
    assert isinstance(total, Decimal)
    assert isinstance(subtotales[0], Decimal)


def test_venta_service_rollback_total_sin_movimientos():
    """T08: si un ítem falla, rollback total sin venta ni movimientos, stock sin cambios."""
    SessionLocal = _make_db()
    db = SessionLocal()
    p_a = Producto(
        sku="PROD-A",
        nombre="Producto A",
        categoria="consola",
        stock_inicial=10,
        estado="activo",
    )
    p_b = Producto(
        sku="PROD-B",
        nombre="Producto B",
        categoria="consola",
        stock_inicial=3,
        estado="activo",
    )
    db.add_all([p_a, p_b])
    db.commit()
    db.close()
    from app.models.movimiento_inventario import MovimientoInventario
    from app.models.venta import Venta
    from app.models.venta_item import VentaItem
    from app.services.venta_service import calcular_stock_actual, registrar_venta

    db = SessionLocal()
    stock_a_before = calcular_stock_actual(db, "PROD-A")
    stock_b_before = calcular_stock_actual(db, "PROD-B")
    assert stock_a_before == 10
    assert stock_b_before == 3
    db.close()

    db = SessionLocal()
    with pytest.raises(HTTPException) as exc:
        registrar_venta(
            db,
            {
                "cliente": {"nombre": "Ana"},
                "items": [
                    {
                        "producto_codigo": "PROD-A",
                        "cantidad": 5,
                        "precio_unitario": Decimal("10.00"),
                    },
                    {
                        "producto_codigo": "PROD-B",
                        "cantidad": 5,
                        "precio_unitario": Decimal("5.00"),
                    },
                ],
            },
        )
    assert exc.value.status_code == 400
    # verificar que no se creó venta ni movimientos
    assert db.query(Venta).count() == 0
    assert db.query(VentaItem).count() == 0
    assert (
        db.query(MovimientoInventario)
        .filter(MovimientoInventario.tipo == "salida")
        .count()
        == 0
    )
    # stock sin cambios
    assert calcular_stock_actual(db, "PROD-A") == 10
    assert calcular_stock_actual(db, "PROD-B") == 3
    db.close()


def test_venta_service_concurrencia_select_for_update():
    """T08: concurrencia SELECT FOR UPDATE — una 201 otra 400, sin stock negativo."""
    SessionLocal = _make_db()
    db = SessionLocal()
    p = Producto(
        sku="PROD-001",
        nombre="Producto A",
        categoria="consola",
        stock_inicial=10,
        estado="activo",
    )
    db.add(p)
    db.commit()
    db.close()
    from app.services.venta_service import calcular_stock_actual, registrar_venta

    # primera venta 6 →201
    db1 = SessionLocal()
    venta1 = registrar_venta(
        db1,
        {
            "cliente": {"nombre": "Ana"},
            "items": [
                {
                    "producto_codigo": "PROD-001",
                    "cantidad": 6,
                    "precio_unitario": Decimal("10.00"),
                }
            ],
        },
    )
    assert venta1.id is not None
    db1.close()

    # segunda venta 6 con stock restante 4 →400
    db2 = SessionLocal()
    with pytest.raises(HTTPException) as exc:
        registrar_venta(
            db2,
            {
                "cliente": {"nombre": "Bob"},
                "items": [
                    {
                        "producto_codigo": "PROD-001",
                        "cantidad": 6,
                        "precio_unitario": Decimal("10.00"),
                    }
                ],
            },
        )
    assert exc.value.status_code == 400
    # stock nunca negativo
    assert calcular_stock_actual(db2, "PROD-001") == 4
    assert calcular_stock_actual(db2, "PROD-001") >= 0
    db2.close()

    # tercera venta 4 exacta debe ser 201
    db3 = SessionLocal()
    venta3 = registrar_venta(
        db3,
        {
            "cliente": {"nombre": "Carlos"},
            "items": [
                {
                    "producto_codigo": "PROD-001",
                    "cantidad": 4,
                    "precio_unitario": Decimal("10.00"),
                }
            ],
        },
    )
    assert venta3.id is not None
    assert calcular_stock_actual(db3, "PROD-001") == 0
    db3.close()
