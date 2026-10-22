# Proposal: PostgreSQL-Only Migration

## Intent

Make PostgreSQL 18 the only runtime and migration target for Nexus, and move the existing `nexus.db` SQLite snapshot to PostgreSQL through a deterministic, auditable, offline process. The change removes accidental SQLite selection, protects append-only inventory and sales history, and establishes measurable cutover and rollback evidence without accessing production or handling credentials in the implementation.

## Scope

### In Scope

- Enforce PostgreSQL-only configuration in the application runtime, SQLAlchemy setup, Alembic online/offline modes, and CI; remove the committed SQLite migration URL and CI SQLite database dependency.
- Audit the complete Alembic chain and model metadata for PostgreSQL 18 compatibility without rewriting applied migrations; add only necessary forward migrations.
- Define a deterministic export/import utility for `nexus.db` with a write freeze, explicit parent-to-child load order, preserved IDs, timestamps, foreign keys, nullable values, `Decimal` values, password hashes, and historical hashes.
- Validate source and target schema revisions, row counts, canonical checksums, foreign keys, append-only invariants, timestamp/decimal semantics, and repaired PostgreSQL sequences.
- Rehearse locally against disposable PostgreSQL 18, provide migration fixtures and tests, update CI, and document dry run, cutover, validation, operational rollback, archive retention, and credential injection.
- Retain `nexus.db` and migration evidence as a read-only archive after acceptance; do not modify or delete the source snapshot or historical records.

### Out of Scope

- Any production connection, production execution, credential discovery, or remote data transfer by this change's implementation work.
- Dual-write, live replication, or a zero-downtime migration bridge.
- Recreating users from plaintext credentials, importing pytest fixtures, or migrating generated/CI data.
- Changes to stock calculation, sale semantics, or the independent `backend-frontend-replacement` change.
- Destructive downgrade rollback, deletion of SQLite history, or rewriting already-applied Alembic revisions.

## Capabilities

### New Capabilities

- `postgresql-only-runtime`: The application, Alembic, and CI accept and provision PostgreSQL 18 only, with safe environment-based credential delivery.
- `offline-data-migration`: A deterministic, repeatable SQLite snapshot export/import contract performs a write-frozen migration while preserving application data and historical identity.
- `migration-validation-and-cutover`: Machine-readable parity checks, sequence repair, acceptance gates, archive handling, and operational rollback govern rehearsal and cutover.

### Modified Capabilities

- None identified in `openspec/specs/`; the existing inventory and sales traceability contract remains authoritative and is preserved rather than relaxed.

## Approach

1. Establish the PostgreSQL-only boundary at configuration and composition points: require a PostgreSQL URL in every environment, remove SQLite-specific engine behavior, inject the approved URL into Alembic, and provision PostgreSQL 18 in CI.
2. Audit models and every migration for PostgreSQL behavior, including checks, timezone-aware timestamps, numeric precision, indexes, foreign keys, and append-only constraints. Preserve applied revision history and use forward-only migrations only when required.
3. Snapshot and identify `nexus.db` by path, size, hash, schema revision, and export timestamp without changing it. During an explicitly approved write freeze, export canonical rows in a deterministic format and order: `usuarios`, `productos`, `proveedores`, `movimientos_inventario`, `ventas`, then `venta_items`.
4. Create the PostgreSQL schema with Alembic, import all six application tables (including empty sales tables), preserve IDs/timestamps/FKs/NULLs/Decimal values/password hashes, and repair each identity sequence to a value above `MAX(id)`.
5. Emit a manifest containing source/target metadata, counts, canonical checksums, sequence state, and validation results. Block acceptance on any mismatch, orphan, timestamp/timezone ambiguity, decimal loss, duplicate, mutable historical row, or incomplete table.
6. Rehearse the exact process against disposable PostgreSQL 18, then document an authorized operational cutover. If acceptance fails, stop target writes and route back only while the preserved SQLite snapshot remains authoritative; retain target evidence and reconcile any accepted target writes append-only before retrying.

The following decisions remain open and MUST be resolved before implementation or cutover: timezone interpretation for existing naive SQLite timestamps; PostgreSQL database name, role, schema, and credential delivery; checksum algorithm/version and canonical serialization; archive retention period and access controls; whether SQLite remains allowed only for isolated unit tests; exact write-freeze procedure and tolerated downtime; and whether any non-application SQLite tables are intentionally excluded after a complete schema audit.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `app/config.py`, `app/database.py` | Modified | Require PostgreSQL URLs and remove SQLite defaults, branches, and runtime fallback without logging secrets. |
| `alembic.ini`, `alembic/env.py`, `alembic/versions/` | Modified | Consume the approved PostgreSQL URL, reject SQLite, and verify the chain against PostgreSQL 18 without rewriting applied revisions. |
| `app/models/` | Modified/verified | Align PostgreSQL metadata for `DateTime(timezone=True)`, `Numeric(12, 2)`, indexes, constraints, and restricted relationships. |
| `scripts/` or migration utility module | New | Implement deterministic snapshot identification, ordered import, canonical manifests, validation, sequence repair, dry run, and write-freeze controls. |
| `tests/conftest.py`, database tests, migration fixtures | Modified/New | Use disposable PostgreSQL fixtures for database behavior; retain SQLite fixtures only if the open test-only policy permits them. Add parity, FK, decimal, timestamp, ID, sequence, append-only, and concurrency coverage. |
| `.github/workflows/ci.yml` | Modified | Run PostgreSQL 18, apply Alembic, execute migration rehearsal/verification, and remove the SQLite database dependency. |
| `.env.example`, `README`, `docs/` migration runbook | Modified/New | Document safe URL/credential injection, dry run, freeze, cutover, validation, rollback, archive retention, and no-production-access boundaries. |
| `nexus.db` and migration evidence | Preserved | Keep the source SQLite snapshot, manifests, checksums, and logs as a read-only audit/rollback archive subject to the approved retention policy. |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| A remaining SQLite default silently recreates `nexus.db` or gives false CI confidence. | High | Reject SQLite at every configuration and migration boundary; assert PostgreSQL 18 in CI and test startup failure for SQLite URLs. |
| SQLite-oriented Alembic checks or batch operations behave differently on PostgreSQL. | Medium | Audit the full chain, preserve applied revisions, rehearse from a clean PostgreSQL 18 schema, and add forward-only corrections only when evidenced. |
| Naive timestamps are assigned the wrong timezone or shifted. | High | Make timezone interpretation an explicit approval gate; canonicalize and compare timestamps before import. |
| Preserved IDs collide with PostgreSQL-generated IDs. | Medium | Set every sequence above `MAX(id)`, record sequence values, and test the next insert for each populated table. |
| Writes during migration cause missing, duplicate, or divergent rows. | High | Require a documented write freeze, immutable source snapshot, deterministic checksums, and acceptance gates before cutover. |
| PostgreSQL-only fixtures increase CI cost or obscure unit-test intent. | Medium | Separate unit fixtures from database integration fixtures and leave SQLite test-only usage as an explicit unresolved decision. |
| Archive or migration logs expose secrets or become unavailable for rollback. | Low/Medium | Inject credentials through approved environment/CI mechanisms, redact URLs and logs, preserve immutable evidence, and finalize retention/access controls before cutover. |

## Rollback Plan

Rollback is operational and non-destructive. Before acceptance, stop target writes, preserve the target database and all manifests/logs for diagnosis, and route the application back to the unchanged SQLite snapshot only under the approved rollback procedure. Do not delete or downgrade target data. Any writes accepted on PostgreSQL must be captured and reconciled as append-only records before another migration attempt. The SQLite file remains the authoritative rollback source until parity, cutover acceptance, and the retention decision are complete; after acceptance PostgreSQL becomes the sole application database and the SQLite file remains read-only archive evidence.

## Dependencies

- PostgreSQL 18 for local rehearsal and CI service provisioning.
- An authorized target `DATABASE_URL` and approved database/role/schema/credential delivery supplied by the owner; this proposal does not discover or invent them.
- A complete SQLite schema audit, approved timezone policy, checksum specification, write-freeze owner/procedure, and archive retention/access policy.
- Alembic and SQLAlchemy behavior compatible with the project's pinned Python 3.11+ dependency set.

## Success Criteria

- [ ] Application startup, Alembic online/offline execution, and CI fail deterministically for every SQLite URL and succeed only with PostgreSQL 18.
- [ ] A clean PostgreSQL 18 rehearsal applies the complete Alembic chain successfully and creates all six application tables, including empty `ventas` and `venta_items`.
- [ ] The migration manifest records source identity, schema revision, export metadata, per-table counts, canonical checksums, FK results, timestamp/Decimal policy, and post-import sequence values; all checks pass with zero orphaned references.
- [ ] Every migrated ID, timestamp, nullable value, monetary `Decimal`, password hash, FK, movement, and sale row matches the approved source snapshot; no historical movement or sale is updated or deleted.
- [ ] Each populated table's next generated ID is greater than its imported maximum, and sequence-repair tests pass.
- [ ] CI runs PostgreSQL-backed integration and migration tests, while any remaining SQLite use is explicitly limited to the approved unit-test policy and never runtime, Alembic, or CI database provisioning.
- [ ] The documented write-freeze cutover and rollback runbooks are dry-run validated, credentials are absent from source/logs, and `nexus.db` is retained as a read-only archive under the approved policy.
