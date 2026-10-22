"""Explicit request-scoped SQLAlchemy transaction ownership."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session


class UnitOfWork:
    """Own one session lifecycle and the single commit/rollback decision."""

    def __init__(
        self,
        session: Session | None = None,
        session_factory: Callable[[], Session] | None = None,
    ):
        if session is None and session_factory is None:
            raise ValueError("A session or session factory is required")
        self.session = session or session_factory()  # type: ignore[misc]
        self._owns_session = session is None
        self._committed = False

    def __enter__(self) -> "UnitOfWork":
        return self

    def commit(self) -> None:
        self.session.commit()
        self._committed = True

    def rollback(self) -> None:
        self.session.rollback()

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if exc_type is not None or not self._committed:
            self.rollback()
        if self._owns_session:
            self.session.close()
