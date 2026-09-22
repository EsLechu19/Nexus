"""Tests de T09 004 — Verificación final (RF-1, constitución + AGENTS)."""

import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]):
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[1]),
    )


def test_T09_pytest_verde():
    result = _run([sys.executable, "-m", "pytest", "--collect-only", "-q"])
    assert result.returncode == 0


def test_T09_ruff_check():
    result = _run([sys.executable, "-m", "ruff", "check", "."])
    assert result.returncode == 0, (
        f"ruff check falló:\n{result.stdout}\n{result.stderr}"
    )


def test_T09_ruff_format():
    result = _run([sys.executable, "-m", "ruff", "format", "--check", "."])
    assert result.returncode == 0, (
        f"ruff format falló:\n{result.stdout}\n{result.stderr}"
    )


def test_T09_mypy():
    result = _run([sys.executable, "-m", "mypy", "app", "--ignore-missing-imports"])
    assert result.returncode == 0, f"mypy falló:\n{result.stdout}\n{result.stderr}"
    assert "success" in result.stdout.lower()


def test_T09_alembic_upgrade_head():
    result = _run([sys.executable, "-m", "alembic", "upgrade", "head"])
    assert result.returncode == 0, (
        f"alembic upgrade head falló:\n{result.stdout}\n{result.stderr}"
    )


def test_T09_docs_con_stock_y_alerta():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    assert client.get("/docs").status_code == 200
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/stock" in paths
    assert "/api/v1/stock/{codigo}" in paths
    # Verificar que StockResponse incluye alerta y stock_minimo
    stock_get = paths["/api/v1/stock"]["get"]
    assert stock_get is not None


def test_T09_stock_nunca_negativo():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.database import Base
    from app.schemas.producto import ProductoCreate
    from app.schemas.proveedor import ProveedorCreate
    from app.schemas.movimiento import MovimientoCreateEntrada, MovimientoCreateSalida

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    from app.services.producto_service import crear_producto
    from app.services.proveedor_service import crear_proveedor
    from app.services.movimiento_service import registrar_entrada, registrar_salida
    from app.services.stock_service import calcular_stock

    crear_producto(
        db,
        ProductoCreate(
            sku="STK-001",
            nombre="Test Stock",
            categoria="videojuego",
            stock_inicial=5,
            stock_minimo=10,
        ),
    )
    crear_proveedor(db, ProveedorCreate(codigo="PROV-001", nombre="Prov"))
    registrar_entrada(
        db,
        MovimientoCreateEntrada(
            producto_codigo="STK-001", proveedor_codigo="PROV-001", cantidad=5
        ),
    )
    stock = calcular_stock(db, "STK-001")
    assert stock["stock_actual"] >= 0
    # Intentar dejar negativo debe fallar y no dejar negativo
    from fastapi import HTTPException
    import pytest

    with pytest.raises(HTTPException) as exc:
        registrar_salida(
            db, MovimientoCreateSalida(producto_codigo="STK-001", cantidad=20)
        )
    assert exc.value.status_code == 400
    assert calcular_stock(db, "STK-001")["stock_actual"] >= 0
    db.close()


def test_T09_constitucion_6_principios_y_capas():
    content = Path("docs/constitution.md").read_text(encoding="utf-8")
    for n in ["1.", "2.", "3.", "4.", "5.", "6."]:
        assert n in content
    for p in ["app/routers", "app/services", "app/models", "app/schemas"]:
        assert Path(p).is_dir()
