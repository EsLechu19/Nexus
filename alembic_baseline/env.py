"""Entorno Alembic para el baseline PostgreSQL de bases nuevas."""

from logging.config import fileConfig

from alembic import context
from alembic.util import CommandError
from sqlalchemy import create_engine, inspect, pool, text

from app.config import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def database_url() -> str:
    """Obtiene la URL validada sin crear un engine en modo offline."""
    return get_settings().database_url


def _command_name() -> str | None:
    """Identifica el comando Alembic sin depender de su representación CLI."""
    import sys

    command_options = getattr(config, "cmd_opts", None)
    command = getattr(command_options, "cmd", None)
    if isinstance(command, str):
        return command
    command_name = getattr(command, "__name__", None)
    if command_name:
        return command_name
    for candidate in ("upgrade", "current", "stamp"):
        if candidate in sys.argv:
            return candidate
    return None


def _reject_non_empty_database(connection) -> None:
    """Protege ``upgrade`` y habilita inspección/reparación controladas."""
    if connection.dialect.name != "postgresql":
        raise CommandError("El baseline solo admite PostgreSQL; SQLite está rechazado")

    tables = inspect(connection).get_table_names(schema="public")
    command = _command_name()
    if command == "current":
        return

    baseline_tables = {
        "productos",
        "proveedores",
        "movimientos_inventario",
        "usuarios",
        "ventas",
        "venta_items",
    }
    if command == "stamp" and baseline_tables.issubset(tables):
        return

    if tables:
        names = ", ".join(sorted(tables))
        if command == "stamp":
            raise CommandError(
                "Solo se permite stamp sobre el esquema baseline completo; "
                "no se modificó la base."
            )
        raise CommandError(
            "El baseline solo se aplica a una base PostgreSQL vacía; "
            f"se encontraron tablas: {names}. No se modificó la base."
        )


def _assert_upgrade_persisted(connection) -> None:
    """Evita informar éxito si el DDL o la revisión no quedaron persistidos."""
    expected_tables = {
        "productos",
        "proveedores",
        "movimientos_inventario",
        "usuarios",
        "ventas",
        "venta_items",
    }
    tables = set(inspect(connection).get_table_names(schema="public"))
    missing_tables = expected_tables - tables
    if missing_tables:
        missing = ", ".join(sorted(missing_tables))
        raise CommandError(
            "El baseline terminó sin persistir todas las tablas esperadas; "
            f"faltan: {missing}."
        )

    version = connection.execute(
        text("SELECT version_num FROM public.alembic_version")
    ).scalar_one_or_none()
    if version != "000000000001":
        raise CommandError(
            "El baseline terminó sin persistir la fila esperada en "
            "public.alembic_version."
        )


def run_migrations_offline() -> None:
    """Genera SQL sin abrir conexiones; no aplica el baseline a una base."""
    context.configure(
        url=database_url(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Valida PostgreSQL y una base vacía antes de crear el esquema."""
    connectable = create_engine(database_url(), poolclass=pool.NullPool)
    try:
        # engine.begin() es la frontera transaccional de SQLAlchemy: confirma
        # DDL y alembic_version juntos solo después de completar la migración.
        # La confirmación manual queda fuera del contexto de Alembic.
        with connectable.begin() as connection:
            _reject_non_empty_database(connection)
            context.configure(connection=connection, transactional_ddl=True)
            context.run_migrations()
            if _command_name() == "upgrade":
                _assert_upgrade_persisted(connection)
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
