# Phase 1 safety-seam evidence

## Implemented seams

- `app/config.py` validates environment-driven database and JWT configuration;
  production rejects SQLite and diagnostics never contain values.
- `app/services/unit_of_work.py` makes session, commit, rollback, and close
  ownership explicit for the characterized sale mutation.
- `app/services/movimiento_service.py` exposes `preparar_salida`, an operation
  that adds and flushes a movement without independently committing.
- `app/services/venta_service.py` uses that canonical operation inside one
  unit of work, preserving sale/item/movement atomicity and traceability.
- `app/compatibility.py` provides a single field-selection presenter seam.
- `app/cutover.py` defaults missing or invalid capability switches to the
  known-good route and emits a structured route decision.
- `app/observability.py` emits local JSON signals while dropping credentials,
  tokens, and authorization material.

## Evidence and limitations

Focused safety and legacy auth/sale tests pass locally. Authentication remains
before protected business dependencies because `get_current_user` performs no
database work. SQLite is used for fast tests only. An authorized PostgreSQL
environment was not available in this apply run, so concurrency rehearsal and
the final Phase 1 gate remain blocked; no production data or database was
accessed.

The existing documented limitations remain: no roles, revocation, refresh,
rate limiting, production observability sink, or deployment-owned
last-known-good version was introduced by this phase.
