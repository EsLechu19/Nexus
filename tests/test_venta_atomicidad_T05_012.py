"""Tests de T05 — venta_service registrar_venta transacción atómica (RF-2, RNF-2, RNF-3) — TDD."""

from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.movimiento_inventario import MovimientoInventario
from app.models.producto import Producto
from app.models.venta import Venta
from app.models.venta_item import VentaItem


def _make_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal


def _crear_productos(SessionLocal):
    db = SessionLocal()
    p1 = Producto(
        sku="PROD-A",
        nombre="Producto A",
        categoria="consola",
        stock_inicial=10,
        estado="activo",
    )
    p2 = Producto(
        sku="PROD-B",
        nombre="Producto B",
        categoria="consola",
        stock_inicial=3,
        estado="activo",
    )
    db.add_all([p1, p2])
    db.commit()
    db.close()


def test_registrar_venta_ok_crea_venta_y_movimientos(monkeypatch):
    """T05: registrar_venta válida crea venta y N movimientos salida, stock descontado."""
    from app.services.venta_service import registrar_venta

    _, SessionLocal = _make_db()
    _crear_productos(SessionLocal)
    db = SessionLocal()
    datos = {
        "cliente": {"nombre": "Ana", "email": "ana@correo.com"},
        "items": [
            {
                "producto_codigo": "PROD-A",
                "cantidad": 2,
                "precio_unitario": Decimal("10.00"),
            },
            {
                "producto_codigo": "PROD-B",
                "cantidad": 1,
                "precio_unitario": Decimal("5.00"),
            },
        ],
    }
    # Necesitamos mockear auth? No, venta_service no requiere auth, solo DB
    venta = registrar_venta(db, datos)
    assert venta.id is not None
    assert venta.cliente_nombre == "Ana"
    assert venta.total == Decimal("25.00")
    # verificar venta_items
    items = db.query(VentaItem).filter(VentaItem.venta_id == venta.id).all()
    assert len(items) == 2
    assert sorted([i.cantidad for i in items]) == [1, 2]
    # movimientos
    movs = (
        db.query(MovimientoInventario)
        .filter(MovimientoInventario.tipo == "salida")
        .all()
    )
    assert len(movs) == 2
    # stock: PROD-A 10-2=8, PROD-B 3-1=2
    from app.services.venta_service import calcular_stock_actual

    assert calcular_stock_actual(db, "PROD-A") == 8
    assert calcular_stock_actual(db, "PROD-B") == 2
    db.close()


def test_registrar_venta_stock_insuficiente_rollback_total():
    """T05: si un ítem no tiene stock, no se crea venta ni ningún movimiento, stock sin cambios."""
    from app.services.venta_service import calcular_stock_actual, registrar_venta

    _, SessionLocal = _make_db()
    _crear_productos(SessionLocal)
    db = SessionLocal()
    # stock PROD-A 10, PROD-B 3
    datos = {
        "cliente": {"nombre": "Ana"},
        "items": [
            {
                "producto_codigo": "PROD-A",
                "cantidad": 5,
                "precio_unitario": Decimal("10.00"),
            },  # ok
            {
                "producto_codigo": "PROD-B",
                "cantidad": 5,
                "precio_unitario": Decimal("5.00"),
            },  # stock 3, pide 5 -> falla
        ],
    }
    stock_a_before = calcular_stock_actual(db, "PROD-A")
    stock_b_before = calcular_stock_actual(db, "PROD-B")
    assert stock_a_before == 10
    assert stock_b_before == 3

    with pytest.raises(HTTPException) as exc:
        registrar_venta(db, datos)
    assert exc.value.status_code == 400
    assert "PROD-B" in str(exc.value.detail)
    assert "disponible 3" in str(exc.value.detail).lower()

    # verificar rollback: no venta, no movimientos, stock sin cambios
    assert db.query(Venta).count() == 0
    assert db.query(VentaItem).count() == 0
    assert (
        db.query(MovimientoInventario)
        .filter(MovimientoInventario.tipo == "salida")
        .count()
        == 0
    )
    assert calcular_stock_actual(db, "PROD-A") == 10
    assert calcular_stock_actual(db, "PROD-B") == 3
    db.close()


def test_registrar_venta_no_expone_update_delete():
    """T05: service no expone UPDATE/DELETE sobre ventas (append-only)."""
    from pathlib import Path

    content = Path("app/services/venta_service.py").read_text(encoding="utf-8")
    assert "UPDATE ventas" not in content
    assert "DELETE FROM ventas" not in content
    # verificar que no hay función update/delete para ventas
    assert "def actualizar_venta" not in content
    assert "def borrar_venta" not in content
