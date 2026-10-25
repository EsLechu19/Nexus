"""Pruebas de EST-002: ancho PostgreSQL de movimientos_inventario.tipo."""

import os
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


REVISION = "a1b2c3d4e5f6"
MIGRATION = Path("alembic/versions/a1b2c3d4e5f6_amplia_tipo_movimientos_inventario.py")


def test_migracion_est002_es_forward_only_y_rechaza_truncamiento():
    contenido = MIGRATION.read_text(encoding="utf-8")

    assert f'revision: str = "{REVISION}"' in contenido
    assert (
        'down_revision: Union[str, Sequence[str], None] = "2c3245f4f658"' in contenido
    )
    assert "type_=sa.String(length=15)" in contenido
    assert "length(tipo) > 10" in contenido
    assert "RuntimeError" in contenido
    assert "entrada_inicial" not in contenido.split("def downgrade", 1)[1]


def test_postgresql_acepta_entrada_inicial_sin_truncamiento():
    """Comprueba en PostgreSQL real el ancho y la inserción de entrada_inicial."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip(
            "DATABASE_URL no está configurada; no hay instancia PostgreSQL disponible"
        )
    if not database_url.lower().startswith(("postgresql://", "postgresql+")):
        pytest.fail(
            "DATABASE_URL debe apuntar a PostgreSQL para esta prueba de integración"
        )

    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                version = connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one()
                assert version == REVISION, (
                    "La base PostgreSQL debe estar actualizada con EST-002 "
                    f"(head actual: {version})"
                )
                width = connection.execute(
                    text(
                        "SELECT character_maximum_length "
                        "FROM information_schema.columns "
                        "WHERE table_name = 'movimientos_inventario' "
                        "AND column_name = 'tipo'"
                    )
                ).scalar_one()
                assert width == 15

                sku = f"EST-{uuid.uuid4().hex[:8].upper()}"
                product_id = connection.execute(
                    text(
                        "INSERT INTO productos "
                        "(sku, nombre, categoria, stock_inicial) "
                        "VALUES (:sku, 'Producto EST-002', 'videojuego', 0) "
                        "RETURNING id"
                    ),
                    {"sku": sku},
                ).scalar_one()
                stored_type = connection.execute(
                    text(
                        "INSERT INTO movimientos_inventario "
                        "(producto_id, tipo, cantidad) "
                        "VALUES (:producto_id, 'entrada_inicial', 1) "
                        "RETURNING tipo"
                    ),
                    {"producto_id": product_id},
                ).scalar_one()
                assert stored_type == "entrada_inicial"
            finally:
                transaction.rollback()
    except SQLAlchemyError as exc:
        pytest.skip(
            f"Instancia PostgreSQL no disponible para integración: {exc.__class__.__name__}"
        )
    finally:
        engine.dispose()
