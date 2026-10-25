"""Pruebas de las barreras de seguridad del baseline PostgreSQL."""

import ast
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.config import ConfigurationError, validate_database_url


ROOT = Path(__file__).resolve().parents[1]


def _baseline_guard():
    source = (ROOT / "alembic_baseline" / "env.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name in {"_command_name", "_reject_non_empty_database"}
    ]
    namespace = {
        "inspect": lambda connection: None,
        "CommandError": RuntimeError,
        "config": type("Config", (), {"cmd_opts": None})(),
    }
    exec(
        compile(ast.Module(body=functions, type_ignores=[]), "env.py", "exec"),
        namespace,
    )
    return namespace["_reject_non_empty_database"], namespace


class _Dialect:
    name = "postgresql"


class _Connection:
    def __init__(self) -> None:
        self.dialect = _Dialect()


def test_baseline_rechaza_sqlite_antes_de_inspeccionar_tablas() -> None:
    guard, namespace = _baseline_guard()
    namespace["inspect"] = lambda connection: None
    connection = _Connection()
    connection.dialect.name = "sqlite"

    with pytest.raises(RuntimeError, match="solo admite PostgreSQL"):
        guard(connection)


def test_baseline_rechaza_base_con_tablas_existentes() -> None:
    guard, namespace = _baseline_guard()

    class Inspector:
        def get_table_names(self, schema):
            assert schema == "public"
            return ["productos"]

    namespace["inspect"] = lambda connection: Inspector()

    with pytest.raises(RuntimeError, match="base PostgreSQL vacía"):
        guard(_Connection())


@pytest.mark.parametrize("command", ["current", "stamp"])
def test_baseline_no_bloquea_current_ni_stamp_en_esquema_existente(command) -> None:
    guard, namespace = _baseline_guard()

    class Inspector:
        def get_table_names(self, schema):
            assert schema == "public"
            return [
                "productos",
                "proveedores",
                "movimientos_inventario",
                "usuarios",
                "ventas",
                "venta_items",
            ]

    namespace["inspect"] = lambda connection: Inspector()
    namespace["config"].cmd_opts = type("CommandOptions", (), {"cmd": command})()

    guard(_Connection())


def test_baseline_sigue_rechazando_upgrade_sobre_esquema_existente() -> None:
    guard, namespace = _baseline_guard()

    class Inspector:
        def get_table_names(self, schema):
            return ["productos"]

    namespace["inspect"] = lambda connection: Inspector()
    namespace["config"].cmd_opts = type("CommandOptions", (), {"cmd": "upgrade"})()

    with pytest.raises(RuntimeError, match="base PostgreSQL vacía"):
        guard(_Connection())


def test_configuracion_rechaza_sqlite_sin_crear_engine() -> None:
    with pytest.raises(ConfigurationError, match="PostgreSQL"):
        validate_database_url("sqlite:///nexus.db")


def test_migracion_raiz_construye_esquema_actual() -> None:
    migration = (
        ROOT / "alembic_baseline" / "versions" / "000000000001_baseline_postgresql.py"
    ).read_text(encoding="utf-8")

    assert "down_revision = None" in migration
    for table in (
        "productos",
        "proveedores",
        "movimientos_inventario",
        "usuarios",
        "ventas",
        "venta_items",
    ):
        assert f'"{table}"' in migration
    assert "sa.String(length=15)" in migration
    assert "entrada_inicial" in migration


def test_online_upgrade_verifica_ddl_y_version_persistidos() -> None:
    source = (ROOT / "alembic_baseline" / "env.py").read_text(encoding="utf-8")

    assert "with connectable.begin() as connection" in source
    assert "transactional_ddl=True" in source
    assert "_assert_upgrade_persisted(connection)" in source
    assert "connection.commit()" not in source


def test_online_upgrade_real_requiere_postgresql_de_prueba() -> None:
    database_url = os.environ.get("NEXUS_BASELINE_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip(
            "PostgreSQL no disponible: defina NEXUS_BASELINE_TEST_DATABASE_URL "
            "apuntando a una base de prueba vacía"
        )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "alembic-baseline.ini",
            "upgrade",
            "head",
        ],
        cwd=ROOT,
        env={**os.environ, "DATABASE_URL": database_url},
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Running upgrade" in result.stderr

    from sqlalchemy import create_engine, inspect, text

    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            tables = set(inspect(connection).get_table_names(schema="public"))
            assert {
                "productos",
                "proveedores",
                "movimientos_inventario",
                "usuarios",
                "ventas",
                "venta_items",
                "alembic_version",
            } <= tables
            assert (
                connection.execute(
                    text("SELECT version_num FROM public.alembic_version")
                ).scalar_one()
                == "000000000001"
            )
    finally:
        engine.dispose()
