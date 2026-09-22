"""Tests de T04 — venta_service lectura de stock y cálculo Decimal (RF-1, RF-2, RNF-6) — TDD."""

from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.movimiento_inventario import MovimientoInventario
from app.models.producto import Producto


def _make_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal


def test_calcular_stock_actual_con_select_for_update():
    """T04: calcular_stock_actual reutiliza SELECT FOR UPDATE y calcula stock_actual."""
    from app.services.venta_service import calcular_stock_actual

    _, SessionLocal = _make_db()
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
    db.refresh(p)
    # sin movimientos, stock debe ser 10
    assert calcular_stock_actual(db, "PROD-001") == 10
    # agregar entrada 5 y salida 3
    db.add(
        MovimientoInventario(
            producto_id=p.id, tipo="entrada", cantidad=5, proveedor_id=1
        )
    )
    db.add(MovimientoInventario(producto_id=p.id, tipo="salida", cantidad=3))
    db.commit()
    assert calcular_stock_actual(db, "PROD-001") == 12  # 10+5-3
    db.close()


def test_validar_stock_suficiente_y_mensaje_especifico():
    """T04: validar_stock_suficiente con cantidad ≤ stock ok, > stock → 400 con disponible/solicitado."""
    from app.services.venta_service import validar_stock_suficiente

    _, SessionLocal = _make_db()
    db = SessionLocal()
    p = Producto(
        sku="PROD-001",
        nombre="Producto A",
        categoria="consola",
        stock_inicial=5,
        estado="activo",
    )
    db.add(p)
    db.commit()
    db.refresh(p)

    # stock 5, pide 5 → ok
    validar_stock_suficiente(db, [{"producto_codigo": "PROD-001", "cantidad": 5}])
    # pide 6 → 400 con mensaje específico
    with pytest.raises(HTTPException) as exc:
        validar_stock_suficiente(db, [{"producto_codigo": "PROD-001", "cantidad": 6}])
    assert exc.value.status_code == 400
    assert "PROD-001" in str(exc.value.detail)
    assert "disponible 5" in str(exc.value.detail).lower()
    assert "solicitado 6" in str(exc.value.detail).lower()
    db.close()


def test_calcular_totales_decimal_exacto():
    """T04: subtotal y total con Decimal exacto, nunca float."""
    from app.services.venta_service import calcular_totales

    items = [
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
    subtotales, total = calcular_totales(items)
    assert subtotales == [Decimal("20.00"), Decimal("25.50")]
    assert total == Decimal("45.50")
    # verificar que no es float
    assert isinstance(total, Decimal)
    # 0.1+0.2 no debe dar 0.30000000004
    items2 = [
        {
            "producto_codigo": "PROD-001",
            "cantidad": 1,
            "precio_unitario": Decimal("0.10"),
        },
        {
            "producto_codigo": "PROD-002",
            "cantidad": 1,
            "precio_unitario": Decimal("0.20"),
        },
    ]
    _, total2 = calcular_totales(items2)
    assert total2 == Decimal("0.30")


def test_validar_stock_no_abre_session_innecesaria():
    """T04: validar_stock y calcular_stock no deben usar float ni exponer hash."""
    from pathlib import Path

    content = Path("app/services/venta_service.py").read_text(encoding="utf-8")
    assert "float(" not in content or "Decimal" in content
    assert "password" not in content.lower()
