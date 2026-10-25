"""Evidencia focalizada de T1.4: atomicidad y concurrencia PostgreSQL."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

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


def _datos(codigo: str, cantidad: int = 1) -> dict:
    return {
        "cliente": {"nombre": "Ana"},
        "items": [
            {
                "producto_codigo": codigo,
                "cantidad": cantidad,
                "precio_unitario": Decimal("10.00"),
            }
        ],
    }


def _make_sqlite_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _seed_products(SessionLocal):
    db = SessionLocal()
    db.add_all(
        [
            Producto(
                sku="PROD-A",
                nombre="Producto A",
                categoria="consola",
                stock_inicial=10,
                estado="activo",
            ),
            Producto(
                sku="PROD-B",
                nombre="Producto B",
                categoria="consola",
                stock_inicial=3,
                estado="activo",
            ),
        ]
    )
    db.commit()
    db.close()


def test_venta_fallo_inyectado_revierte_todas_las_escrituras(monkeypatch):
    from app.services import movimiento_service
    from app.services.venta_service import registrar_venta

    SessionLocal = _make_sqlite_db()
    _seed_products(SessionLocal)
    db = SessionLocal()
    original = movimiento_service.preparar_salida
    calls = 0

    def fallo_en_segundo_item(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("fallo de persistencia inyectado")
        return original(*args, **kwargs)

    monkeypatch.setattr(movimiento_service, "preparar_salida", fallo_en_segundo_item)

    with pytest.raises(HTTPException) as exc:
        registrar_venta(
            db,
            {
                "cliente": {"nombre": "Ana"},
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
            },
        )

    assert exc.value.status_code == 500
    assert db.query(Venta).count() == 0
    assert db.query(VentaItem).count() == 0
    assert db.query(MovimientoInventario).count() == 0
    db.close()


@pytest.mark.parametrize(
    ("codigo", "estado", "status"),
    [("NO-EXISTE", None, 404), ("PROD-INACTIVO", "inactivo", 400)],
)
def test_venta_producto_invalido_no_deja_efectos(codigo, estado, status):
    from app.services.venta_service import registrar_venta

    SessionLocal = _make_sqlite_db()
    db = SessionLocal()
    if estado:
        db.add(
            Producto(
                sku=codigo,
                nombre="Producto inactivo",
                categoria="consola",
                stock_inicial=10,
                estado=estado,
            )
        )
        db.commit()

    with pytest.raises(HTTPException) as exc:
        registrar_venta(db, _datos(codigo))

    assert exc.value.status_code == status
    assert db.query(Venta).count() == 0
    assert db.query(VentaItem).count() == 0
    assert db.query(MovimientoInventario).count() == 0
    db.close()


def test_venta_usa_un_solo_commit(monkeypatch):
    from app.services.venta_service import registrar_venta

    SessionLocal = _make_sqlite_db()
    _seed_products(SessionLocal)
    db = SessionLocal()
    commits = 0
    original_commit = db.commit

    def contar_commit():
        nonlocal commits
        commits += 1
        original_commit()

    monkeypatch.setattr(db, "commit", contar_commit)
    registrar_venta(db, _datos("PROD-A"))
    assert commits == 1
    db.close()


def test_concurrencia_postgresql_no_permite_stock_negativo():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip(
            "PostgreSQL bloqueado: DATABASE_URL no está disponible en el proceso"
        )
    if not database_url.lower().startswith(("postgresql://", "postgresql+")):
        pytest.skip("PostgreSQL bloqueado: DATABASE_URL no apunta a PostgreSQL")

    from app.services.venta_service import calcular_stock_actual, registrar_venta

    engine = create_engine(database_url, pool_size=4, max_overflow=0)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    codigo = f"PG-{uuid4().hex[:12].upper()}"
    setup = SessionLocal()
    setup.add(
        Producto(
            sku=codigo,
            nombre="Producto concurrencia",
            categoria="consola",
            stock_inicial=10,
            estado="activo",
        )
    )
    setup.commit()
    setup.close()

    barrier = Barrier(2)

    def ejecutar_venta() -> str:
        db = SessionLocal()
        try:
            barrier.wait(timeout=10)
            registrar_venta(db, _datos(codigo, cantidad=6))
            return "ok"
        except HTTPException as exc:
            return f"http:{exc.status_code}"
        finally:
            db.close()

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            resultados = list(executor.map(lambda _: ejecutar_venta(), range(2)))

        assert sorted(resultados) == ["http:400", "ok"]
        verificacion = SessionLocal()
        assert calcular_stock_actual(verificacion, codigo) == 4
        assert (
            verificacion.query(Venta).filter(Venta.cliente_nombre == "Ana").count() >= 1
        )
        verificacion.close()
    finally:
        engine.dispose()
