"""Pruebas de la frontera de configuración PostgreSQL-only."""

import importlib

import pytest

import app.config as config
from app.config import ConfigurationError, Settings, validate_database_url


@pytest.mark.parametrize(
    "value",
    ["", "sqlite:///nexus.db", "mysql://user:password/db", "postgres://user/db"],
)
def test_validate_database_url_rejects_non_postgresql(value):
    with pytest.raises(ConfigurationError, match="DATABASE_URL"):
        validate_database_url(value)


@pytest.mark.parametrize(
    "value",
    [
        "postgresql://user:password@localhost/nexus_dev",
        "postgresql+psycopg2://user:password@localhost/nexus_dev",
    ],
)
def test_validate_database_url_accepts_supported_postgresql(value):
    assert validate_database_url(value) == value


def test_settings_requires_database_url(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "DOTENV_PATH", tmp_path / ".env")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ConfigurationError, match="DATABASE_URL"):
        Settings.from_environment()


def test_settings_loads_dotenv_without_overriding_explicit_environment(
    monkeypatch, tmp_path
):
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "DATABASE_URL=postgresql://dotenv:dotenv@localhost/from_dotenv\n"
        "JWT_SECRET_KEY=dotenv-secret-32-characters-minimum!!\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "DOTENV_PATH", dotenv_path)
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://explicit:explicit@localhost/from_environment"
    )
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    settings = Settings.from_environment()

    assert settings.database_url.endswith("/from_environment")
    assert settings.jwt_secret_key == "dotenv-secret-32-characters-minimum!!"


def test_settings_rejects_sqlite_url_from_dotenv(monkeypatch, tmp_path):
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "DATABASE_URL=sqlite:///private-nexus.db\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "DOTENV_PATH", dotenv_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ConfigurationError, match="DATABASE_URL"):
        Settings.from_environment()


def test_settings_error_does_not_disclose_url(monkeypatch):
    secret_url = "sqlite:///private-nexus.db"
    monkeypatch.setenv("DATABASE_URL", secret_url)

    with pytest.raises(ConfigurationError) as error:
        Settings.from_environment()

    assert secret_url not in str(error.value)


def test_database_has_no_sqlite_connection_arguments(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:password@localhost/nexus_dev")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-32-characters-minimum!!")

    database = importlib.import_module("app.database")
    database = importlib.reload(database)

    assert database.SQLALCHEMY_DATABASE_URL.startswith("postgresql://")
    assert database.engine.url.get_backend_name() == "postgresql"
