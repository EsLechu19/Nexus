"""Regression tests for the Phase 1 safety seams."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import ConfigurationError, Settings
import app.config as config
from app.compatibility import present_compatibly
from app.cutover import select_capability
from app.database import Base
from app.observability import SafeEventLogger
from app.services.unit_of_work import UnitOfWork


def test_settings_rejects_invalid_database_without_disclosing_value(monkeypatch):
    monkeypatch.setattr(config, "DOTENV_PATH", Path("missing-test-env"))
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:secret@example/db")
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ConfigurationError) as error:
        Settings.from_environment()

    assert "JWT_SECRET_KEY" in str(error.value)
    assert "secret" not in str(error.value)


def test_settings_requires_postgres_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///unsafe.db")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-32-characters-minimum!!")

    with pytest.raises(ConfigurationError, match="DATABASE_URL"):
        Settings.from_environment()


def test_unit_of_work_owns_commit_and_rollback():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    with UnitOfWork(session_factory()) as uow:
        assert uow.session.is_active
        uow.commit()

    with pytest.raises(RuntimeError):
        with UnitOfWork(session_factory()):
            raise RuntimeError("expected failure")


def test_safe_event_logger_drops_secret_fields(caplog):
    logger = SafeEventLogger("test.phase1")
    caplog.set_level("INFO", logger="test.phase1")

    logger.emit(
        "auth.failure",
        capability="catalog",
        password="plain-text",
        password_hash="$2b$hash",
        token="jwt",
    )

    message = caplog.records[-1].getMessage()
    assert "plain-text" not in message
    assert "$2b$hash" not in message
    assert "jwt" not in message
    assert "auth.failure" in message


def test_rollback_runbook_preserves_history_boundary():
    runbook = Path("runbooks/phase1-rollback.md").read_text(encoding="utf-8")

    assert "last-known-good" in runbook
    assert "must not" in runbook.lower()
    assert "historical" in runbook.lower()


def test_invalid_capability_switch_falls_back_to_known_good():
    assert select_capability("untrusted", {"catalog-v2"}, "catalog-v1") == "catalog-v1"
    assert select_capability("catalog-v2", {"catalog-v2"}, "catalog-v1") == "catalog-v2"


def test_compatibility_presenter_keeps_documented_fields_only():
    internal = {"id": 7, "total": "10.00", "password_hash": "private"}

    assert present_compatibly(internal, ("id", "total")) == {"id": 7, "total": "10.00"}


def test_auth_dependency_rejects_before_any_database_dependency():
    from fastapi import HTTPException
    from app.services.deps import get_current_user

    with pytest.raises(HTTPException) as error:
        get_current_user(None)

    assert error.value.status_code == 401
