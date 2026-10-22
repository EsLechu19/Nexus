"""Validated environment configuration for application composition."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse


class ConfigurationError(ValueError):
    """Raised when required runtime configuration is unsafe or incomplete."""


@dataclass(frozen=True)
class Settings:
    """Validated settings without exposing secret values."""

    database_url: str
    jwt_secret_key: str | None
    environment: str

    @classmethod
    def from_environment(cls) -> "Settings":
        environment = os.getenv("APP_ENV", "development").strip().lower()
        database_url = os.getenv("DATABASE_URL", "sqlite:///nexus.db").strip()
        if not database_url:
            raise ConfigurationError("DATABASE_URL is required")

        parsed = urlparse(database_url)
        if parsed.scheme not in {"sqlite", "postgresql", "postgres"}:
            raise ConfigurationError("DATABASE_URL has an unsupported scheme")
        if environment == "production" and parsed.scheme == "sqlite":
            raise ConfigurationError("DATABASE_URL must use PostgreSQL in production")

        secret = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
        if environment == "production" and not secret:
            raise ConfigurationError("JWT_SECRET_KEY is required in production")
        if secret is not None and len(secret) < 16:
            raise ConfigurationError("JWT_SECRET_KEY is too short")

        return cls(database_url, secret, environment)


def get_settings() -> Settings:
    """Build and validate settings at the composition boundary."""
    return Settings.from_environment()
