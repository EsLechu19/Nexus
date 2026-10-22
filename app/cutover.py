"""Allowlisted capability routing with a known-good fallback."""

from __future__ import annotations

from app.observability import operations_logger


def select_capability(requested: str | None, allowed: set[str], known_good: str) -> str:
    """Select only approved routes; missing or invalid values stay on known-good."""
    selected = requested if requested in allowed else known_good
    operations_logger.emit(
        "capability.route",
        requested=requested or "missing",
        selected=selected,
        cutover_state="replacement" if selected != known_good else "known-good",
    )
    return selected
