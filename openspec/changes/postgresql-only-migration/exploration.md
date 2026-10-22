# Exploration: PostgreSQL-only migration

## Current State

Nexus currently has a runtime SQLite fallback and a migration configuration that defaults to SQLite:

- `app/config.py` defaults `DATABASE_URL` to `sqlite:///nexus.db`, accepts SQLite and PostgreSQL schemes, and only rejects SQLite in production.
- `app/database.py` conditionally adds SQLite `check_same_thread` arguments and creates the engine directly from settings.
- `alembic.ini` hard-codes `sqlalchemy.url = sqlite:///nexus.db`; `alembic/env.py` reads that value rather than injecting the runtime URL.
- The Alembic chain is at revision `2c3245f4f658` and defines `productos`, `proveedores`, `movimientos_inventario`, `usuarios`, `ventas`, and `venta_items`. Existing migrations contain SQLite-oriented adaptations (`batch_alter_table`, simplified SQLite checks) that must be reviewed against PostgreSQL behavior before applying to a new target.
- `.github/workflows/ci.yml` explicitly provisions SQLite through `DATABASE_URL=sqlite:///nexus.db`, runs Alembic against it, and runs the backend tests against that database.
- Tests mix shared application configuration with isolated in-memory SQLite sessions (`create_engine("sqlite:///:memory:")`). These are test fixtures, not production records, and should be recreated or moved to PostgreSQL-backed test infrastructure rather than migrated.
- The active `backend-frontend-replacement` change already defines data safety, append-only history, checksums/counts, rollback, and PostgreSQL rehearsal principles. This initiative is separate and must not modify that change.

Read-only inspection of `nexus.db` found the following source snapshot:

| Table | Rows | ID range | Notes |
|---|---:|---:|---|
| `productos` | 2 | 1–2 | Preserve IDs and timestamps |
| `proveedores` | 1 | 1–1 | Preserve IDs and timestamps |
| `usuarios` | 3 | 2–4 | Preserve password hashes and IDs; ID 1 is absent |
| `movimientos_inventario` | 2 | 1–2 | Historical append-only evidence |
| `ventas` | 0 | — | Schema must still be created |
| `venta_items` | 0 | — | Schema must still be created |

`alembic_version` reports `2c3245f4f658`. The inspected foreign-key joins have zero orphaned references. Movement and sales rows must be treated as immutable; the source file should remain preserved as a rollback/audit snapshot until parity and cutover acceptance are complete.

The current models use integer primary keys, timezone-declared `DateTime`, and `Numeric(12, 2)` for sales. SQLite currently stores timestamps as naive-looking `YYYY-MM-DD HH:MM:SS` values, so timezone interpretation and normalization must be decided and tested before import. PostgreSQL identity/sequence state must be advanced past imported IDs so future inserts cannot collide.

## Affected Areas

- `app/config.py` — remove the SQLite default and reject SQLite in every environment; require a PostgreSQL URL without logging credentials.
- `app/database.py` — remove SQLite-specific connection behavior and define PostgreSQL engine/session settings explicitly.
- `alembic.ini`, `alembic/env.py` — stop using a committed SQLite URL; make migrations consume the approved environment URL and validate PostgreSQL-only operation.
- `alembic/versions/*.py` — audit the complete chain for PostgreSQL compatibility, especially check expressions, timestamp defaults, foreign keys, and the historical movement batch migration. Do not rewrite applied migrations; add a new forward-only migration only when schema changes are actually required.
- `app/models/` — verify model metadata matches the PostgreSQL target exactly, including `Numeric(12,2)`, `DateTime(timezone=True)`, indexes, constraints, and `ON DELETE RESTRICT` relationships.
- `scripts/` or a dedicated migration utility module (new) — provide a deterministic SQLite export/import workflow with explicit table order, preserved IDs/timestamps/FKs, validation, checksums, counts, and sequence repair. The utility must not alter `nexus.db` or historical rows.
- `tests/conftest.py` and database-dependent tests — separate production-data migration from test fixtures; provide disposable PostgreSQL test setup or a clearly isolated test database. Keep unit tests that intentionally use in-memory SQLite only if the initiative explicitly allows SQLite as a test-only dependency; otherwise replace them with PostgreSQL fixtures.
- Tests covering `app/services/venta_service.py`, `app/services/movimiento_service.py`, and append-only invariants — add migration parity, decimal/timestamp, FK, ID/sequence, and no-update/no-delete checks. Include PostgreSQL concurrency tests for sale stock deduction because SQLite tests cannot prove row-lock behavior.
- `.github/workflows/ci.yml` — run PostgreSQL 18 as a service, provision a test database through CI secrets/environment, apply Alembic, run migrations/import verification, and remove the SQLite database dependency.
- `.env.example`, deployment/run documentation, and `README`/`docs/` migration runbook (where present) — document `DATABASE_URL`, credential injection, backup/export, dry run, cutover, validation, and rollback without embedding credentials.
- `openspec/changes/postgresql-only-migration/` — this exploration and subsequent proposal/spec/design/tasks; keep it independent from `backend-frontend-replacement`.

## Data Migration Boundary

**Migrate from `nexus.db`:** all rows in `productos`, `proveedores`, `usuarios`, `movimientos_inventario`, `ventas`, and `venta_items`, plus their integer IDs, timestamps, nullable values, monetary values, and foreign-key relationships. Empty sales tables still require schema creation and explicit zero-count validation. Preserve password hashes; do not recreate users from plaintext credentials.

**Recreate, do not import:** pytest fixtures, in-memory test rows, generated test users, CI databases, compiled/cache files, and any sample data that is not in `nexus.db`. Test data must be generated by fixtures in the disposable target database. The migration must identify the source snapshot by path, size/hash, schema revision, and export timestamp without copying secrets into logs.

## Approaches

1. **Offline deterministic export/import with a write freeze** — snapshot `nexus.db`, export ordered CSV/JSON or a controlled SQLite reader format, create the PostgreSQL schema with Alembic, load parent tables before child tables, restore IDs/timestamps, repair sequences, then run counts/checksums/FK/append-only validation.
   - Pros: auditable, repeatable, credential-safe, easy to dry-run, and compatible with the current small dataset.
   - Cons: requires a maintenance window and a carefully defined source freeze; timestamp and constraint incompatibilities surface during rehearsal.
   - Effort: Medium.

2. **Direct database dump/restore conversion** — use a generic SQLite-to-PostgreSQL conversion tool or generated SQL dump.
   - Pros: potentially fast for larger datasets and less application code.
   - Cons: weak control over SQLite quirks, constraint ordering, timestamp semantics, sequence repair, checksums, and append-only guarantees; tool availability and output are harder to make deterministic in CI.
   - Effort: Medium/High.

3. **Dual-write or live replication bridge** — write new changes to both databases during a transition.
   - Pros: reduces the final outage window.
   - Cons: unnecessary for the current dataset, introduces reconciliation/idempotency failure modes, and conflicts with the requirement for one authoritative PostgreSQL target unless a separate decision defines dual-write safeguards.
   - Effort: High.

## Recommendation

Use the offline deterministic export/import approach. First make runtime and Alembic PostgreSQL-only, then rehearse the exact migration against a disposable local PostgreSQL 18 database, and only then perform a write-frozen production-like cutover. The importer should load `usuarios`, `productos`, and `proveedores` before `movimientos_inventario`, then `ventas`, then `venta_items`; it must preserve source IDs and timestamps, validate every FK, set PostgreSQL sequences to `MAX(id)`, and emit machine-readable counts/checksums. Checksums should be computed over canonicalized rows with explicit timestamp and decimal serialization so source and target comparison is meaningful.

Rollback is operational, not a destructive downgrade: stop writes to the target, route the application back only while the preserved SQLite snapshot remains authoritative, retain target evidence/logs, and reconcile any accepted target writes as append-only records before retrying. After successful acceptance, PostgreSQL becomes the sole application database and SQLite is retained as a read-only archive until the retention decision is approved.

## Decisions Pending

- PostgreSQL database name, role, schema, and credential delivery mechanism. The agent has no password and must not probe production or invent credentials.
- Whether local PostgreSQL 18 is the rehearsal target and how the user will supply an authorized `DATABASE_URL` for local execution.
- Whether SQLite remains permitted for isolated unit tests, or whether all database tests must run against PostgreSQL 18.
- Exact write-freeze/cutover procedure and maximum tolerated downtime.
- Canonical timezone policy for existing naive SQLite timestamps (for example, interpret as UTC only if verified by the owner).
- Export format and checksum algorithm/version, including treatment of NULLs, decimals, and timestamps.
- Retention period and access controls for `nexus.db`, exported files, logs, and migration manifests.
- Whether any rows outside the six application tables are intentionally excluded after a complete SQLite schema audit.

## Risks

- The committed Alembic URL and CI still select SQLite, so a partial configuration change could produce false migration confidence or silently recreate `nexus.db`.
- Existing SQLite check constraints and batch migration code may not be equivalent on PostgreSQL; applying the chain without a rehearsal can fail or alter accepted data.
- Naive SQLite timestamps may be shifted incorrectly when imported into timezone-aware PostgreSQL columns.
- Preserved IDs without sequence repair can cause future primary-key collisions.
- A live cutover without a write freeze can create missing or duplicated rows and invalidate checksums.
- Replacing SQLite test fixtures wholesale can increase CI cost and conceal whether a failure is a production-data problem or a fixture problem.
- No credentials are available to this agent; no PostgreSQL connection or remote/production access was attempted.

## Ready for Proposal

Yes, with the pending decisions above explicitly recorded. The proposal should define the PostgreSQL-only boundary, the offline migration contract, the validation manifest, the write-freeze rollback procedure, and the test/CI transition before implementation. No source code or the active `backend-frontend-replacement` change was modified.
