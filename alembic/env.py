from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context
from alembic.util import CommandError
from app.config import get_settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from app.database import Base
from app.models import (
    movimiento_inventario,
    producto,
    proveedor,
    usuario,
    venta,
    venta_item,
)

target_metadata = Base.metadata

_OFFLINE_BATCH_REVISIONS = ("9111dba96a53", "7010b4ddca09")


def _reject_unsupported_offline_chain() -> None:
    """Fail explicitly for the historical batch revisions without reflection."""
    command_options = getattr(config, "cmd_opts", None)
    revision_argument = getattr(command_options, "revision", None)
    if isinstance(revision_argument, (list, tuple)):
        revision_argument = revision_argument[-1] if revision_argument else None
    if revision_argument is None:
        revision_argument = context.get_revision_argument()
    if revision_argument is None:
        return

    target_revision = revision_argument.rsplit(":", 1)[-1]
    if target_revision in {"head", "heads", *_OFFLINE_BATCH_REVISIONS}:
        revisions = ", ".join(_OFFLINE_BATCH_REVISIONS)
        raise CommandError(
            "Offline SQL generation is unsupported for the migration chain "
            f"because revisions {revisions} use batch_alter_table(recreate='always') "
            "and require live PostgreSQL reflection. Run this chain online against "
            "a disposable PostgreSQL database. Historical migrations are unchanged."
        )


def database_url() -> str:
    """Return the validated environment URL for both Alembic modes."""
    return get_settings().database_url


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = database_url()
    _reject_unsupported_offline_chain()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(database_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
