"""Tests de T01 — Modelo Usuario (RF-4) — TDD."""

import subprocess
from pathlib import Path


def test_modelo_usuario_existe_y_tabla():
    """T01: app/models/usuario.py define Usuario con tabla usuarios."""
    from app.models.usuario import Usuario

    assert Usuario.__tablename__ == "usuarios"
    assert Usuario.__name__ == "Usuario"


def test_modelo_usuario_columnas_y_tipos():
    """T01: columnas id, email, password_hash, created_at con tipos y constraints."""
    from sqlalchemy import Integer, String

    from app.models.usuario import Usuario

    cols = {c.name: c for c in Usuario.__table__.columns}
    for name in ["id", "email", "password_hash", "created_at"]:
        assert name in cols, f"falta columna {name}"

    assert isinstance(cols["id"].type, Integer)
    assert isinstance(cols["email"].type, String) and cols["email"].type.length == 254
    assert (
        isinstance(cols["password_hash"].type, String)
        and cols["password_hash"].type.length == 72
    )
    from sqlalchemy import DateTime

    assert isinstance(cols["created_at"].type, DateTime)

    for name in ["email", "password_hash", "created_at"]:
        assert not cols[name].nullable, f"{name} debe ser NOT NULL"

    assert list(Usuario.__table__.primary_key.columns)[0].name == "id"


def test_modelo_usuario_email_unique_y_indice():
    """T01: email UNIQUE con índice ix_usuarios_email."""
    from app.models.usuario import Usuario

    email_col = Usuario.__table__.c.email
    assert email_col.unique is True or any(
        idx.unique and email_col in idx.columns.values()
        for idx in Usuario.__table__.indexes
    ), "email debe ser UNIQUE"

    # índice existe
    has_idx = (
        any("ix_usuarios_email" == idx.name for idx in Usuario.__table__.indexes)
        or email_col.unique
    )
    assert has_idx, "falta índice ix_usuarios_email"


def test_modelo_usuario_singular_plural():
    """AGENTS.md: modelo singular Usuario, tabla plural usuarios."""
    from app.models.usuario import Usuario

    assert Usuario.__name__ == "Usuario"
    assert Usuario.__tablename__ == "usuarios"


def test_migracion_usuarios_existe():
    """T01: existe migración crea usuarios 011 con tabla usuarios."""
    versions = Path("alembic/versions")
    assert versions.is_dir(), "falta alembic/versions"
    content_all = " ".join(p.read_text(encoding="utf-8") for p in versions.glob("*.py"))
    assert "usuarios" in content_all, "falta tabla usuarios en migraciones"
    assert "ix_usuarios_email" in content_all or "usuarios" in content_all


def test_alembic_upgrade_head_contiene_usuarios():
    """T01: alembic upgrade head aplica migración usuarios sin errores."""
    result = subprocess.run(
        ["python", "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    result2 = subprocess.run(
        ["python", "-m", "alembic", "current"],
        capture_output=True,
        text=True,
    )
    assert result2.returncode == 0
