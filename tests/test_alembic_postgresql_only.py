"""Pruebas de la frontera PostgreSQL-only de Alembic."""

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_alembic(
    *arguments: str, database_url: str
) -> subprocess.CompletedProcess[str]:
    environment = {
        **os.environ,
        "PYTHONPATH": str(ROOT),
        "DATABASE_URL": database_url,
        "JWT_SECRET_KEY": "test-secret-32-characters-minimum!!",
    }
    return subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_alembic_ini_does_not_contain_usable_database_url():
    ini = (ROOT / "alembic.ini").read_text(encoding="utf-8")

    assert "sqlalchemy.url =" not in ini
    assert "sqlite:///" not in ini


def test_alembic_offline_mode_rejects_sqlite_before_rendering():
    result = _run_alembic("upgrade", "head", "--sql", database_url="sqlite:///nexus.db")

    assert result.returncode != 0
    assert "DATABASE_URL" in result.stderr
    assert "sqlite" not in result.stdout.lower()


def test_alembic_offline_mode_uses_environment_postgresql_url():
    result = _run_alembic(
        "upgrade",
        "1a81a5e6e75b",
        "--sql",
        database_url="postgresql://test:test@localhost:5432/nexus_dev",
    )

    assert result.returncode == 0, result.stderr
    assert "Context impl PostgresqlImpl" in result.stderr
    assert "CREATE TABLE productos" in result.stdout


def test_alembic_offline_mode_rejects_historical_batch_chain_explicitly():
    result = _run_alembic(
        "upgrade",
        "head",
        "--sql",
        database_url="postgresql://test:test@localhost:5432/nexus_dev",
    )

    assert result.returncode != 0
    assert "9111dba96a53" in result.stderr
    assert "7010b4ddca09" in result.stderr
    assert "live PostgreSQL reflection" in result.stderr
    assert "CREATE TABLE alembic_version" not in result.stdout
