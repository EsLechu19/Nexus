"""Validated environment configuration for application composition."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from dotenv import dotenv_values


SUPPORTED_DATABASE_SCHEMES = {
    "postgresql",
    "postgresql+psycopg2",
}
DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"


class ConfigurationError(ValueError):
    """Raised when required runtime configuration is unsafe or incomplete."""


def _read_environment() -> dict[str, str]:
    """Read .env values without replacing explicitly provided variables."""
    dotenv_environment = {
        key: value
        for key, value in dotenv_values(DOTENV_PATH).items()
        if value is not None
    }
    return {**dotenv_environment, **os.environ}


def validate_database_url(database_url: str) -> str:
    """Validate and return the PostgreSQL URL used by the application."""
    value = database_url.strip()
    if not value:
        raise ConfigurationError("DATABASE_URL is required")

    scheme = urlparse(value).scheme.lower()
    if scheme not in SUPPORTED_DATABASE_SCHEMES:
        raise ConfigurationError("DATABASE_URL must use PostgreSQL")
    return value


@dataclass(frozen=True)
class Settings:
    """Validated settings without exposing secret values."""

    database_url: str
    jwt_secret_key: str | None
    environment: str

    @classmethod
    def from_environment(cls) -> "Settings":
        environment_values = _read_environment()
        environment = environment_values.get("APP_ENV", "development").strip().lower()
        database_url = validate_database_url(environment_values.get("DATABASE_URL", ""))

        secret = environment_values.get("JWT_SECRET_KEY") or environment_values.get(
            "SECRET_KEY"
        )
        if environment == "production" and not secret:
            raise ConfigurationError("JWT_SECRET_KEY is required in production")
        if secret is not None and len(secret) < 16:
            raise ConfigurationError("JWT_SECRET_KEY is too short")

        return cls(database_url, secret, environment)


def get_settings() -> Settings:
    """Build and validate settings at the composition boundary."""
    return Settings.from_environment()
