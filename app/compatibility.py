"""Compatibility presenters for stable HTTP response boundaries."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def present_compatibly(
    payload: Mapping[str, Any], fields: tuple[str, ...]
) -> dict[str, Any]:
    """Select documented response fields without exposing internal representations."""
    return {field: payload[field] for field in fields if field in payload}
