"""Structured local operational signals with a strict secret denylist."""

from __future__ import annotations

import json
import logging
from typing import Any


_FORBIDDEN_FIELDS = {"password", "password_hash", "token", "secret", "authorization"}


class SafeEventLogger:
    """Emit correlation-safe JSON events without credential material."""

    def __init__(self, name: str = "app.operations") -> None:
        self._logger = logging.getLogger(name)

    def emit(self, event: str, **fields: Any) -> None:
        safe_fields = {
            key: value
            for key, value in fields.items()
            if key.lower() not in _FORBIDDEN_FIELDS
        }
        self._logger.info(json.dumps({"event": event, **safe_fields}, sort_keys=True))


operations_logger = SafeEventLogger()
