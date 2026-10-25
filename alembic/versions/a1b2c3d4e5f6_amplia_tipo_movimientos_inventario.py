"""Amplía el tipo de movimiento a 15 caracteres."""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# Identificadores de revisión usados por Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "2c3245f4f658"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Permite persistir el valor entrada_inicial sin truncamiento."""
    op.alter_column(
        "movimientos_inventario",
        "tipo",
        existing_type=sa.String(length=10),
        type_=sa.String(length=15),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Rechaza el downgrade si puede truncar valores existentes."""
    bind = op.get_bind()
    tiene_valores_largos = bind.execute(
        sa.text("SELECT 1 FROM movimientos_inventario WHERE length(tipo) > 10 LIMIT 1")
    ).first()
    if tiene_valores_largos is not None:
        raise RuntimeError(
            "No se puede reducir movimientos_inventario.tipo a VARCHAR(10): "
            "existen valores que serían truncados."
        )

    op.alter_column(
        "movimientos_inventario",
        "tipo",
        existing_type=sa.String(length=15),
        type_=sa.String(length=10),
        existing_nullable=False,
    )
