# Design: PostgreSQL-Only Migration

## Technical Approach

The change is implemented as three coordinated boundaries: a PostgreSQL-only composition boundary, a pure/offline migration pipeline, and a validation/cutover evidence boundary. The application and Alembic will receive one environment-provided PostgreSQL URL, validate its scheme before creating an engine or rendering SQL, and never retain a SQLite fallback. A dedicated migration package will read a byte-stable `nexus.db` snapshot, export canonical rows without mutating it, import them into a clean PostgreSQL 18 schema in dependency order, repair sequences, and emit a credential-free manifest.

The implementation follows the existing layered backend rather than placing migration behavior in routers or services. Database configuration remains in `app/config.py` and `app/database.py`; migration orchestration belongs under `scripts/` (or a dedicated `app/migration/` package if the implementation needs importable library boundaries); Alembic remains the schema authority. Existing revisions through `2c3245f4f658` are immutable. The current chain is explicitly audited for PostgreSQL behavior, and only an evidenced forward migration may be added.

The source snapshot is identified before export and checked again before import. The authoritative export requires an operator-supplied freeze marker. Export and import are separate stages so dry runs can inspect source identity and canonical data before any target write. Import occurs inside a target transaction where possible; a failed row, FK, duplicate, or policy validation aborts the load and records failure evidence rather than accepting a partial cutover.

## Architecture Decisions

### Decision: Enforce PostgreSQL at the composition boundary

**Choice**: Make `Settings.from_environment()` require `postgresql://` or `postgresql+<driver>://`, reject missing/unsupported/SQLite URLs, and expose one validated URL to both SQLAlchemy and Alembic. Remove `_connect_args` SQLite branching and the committed SQLite URL.

**Alternatives considered**: Keep SQLite in development; accept both schemes and rely on CI; validate only in production.

**Rationale**: The constitution names PostgreSQL as the sole stack, and a permissive development fallback can recreate `nexus.db` or produce false migration confidence. Validation before engine construction gives deterministic failure without opening or creating SQLite files. Driver acceptance must be explicit and limited to the installed PostgreSQL driver.

### Decision: Inject the Alembic URL from the approved environment

**Choice**: `alembic/env.py` reads the validated settings URL, validates it before offline rendering or online engine creation, and overrides the INI value. `alembic.ini` contains no usable database URL.

**Alternatives considered**: Keep `sqlalchemy.url` as a placeholder; duplicate a URL in the INI; use `engine_from_config` with an unvalidated section.

**Rationale**: There must be one source of truth and no credential-bearing URL in version control. Offline mode is still an execution boundary and must reject SQLite before producing migration SQL.

### Decision: Use a controlled deterministic export/import pipeline

**Choice**: Implement a Python utility with separate snapshot, export, import, sequence-repair, validation, and manifest components. Use a versioned canonical row representation rather than a generic dump converter.

**Alternatives considered**: Generic SQLite-to-PostgreSQL dump conversion; dual-write/live replication; direct application-level re-creation of users and transactions.

**Rationale**: The dataset is small, identity and historical values must be preserved, and the process needs reproducible checksums, explicit NULL/Decimal/timestamp semantics, and auditable failure boundaries. A dump tool cannot reliably express these project-specific guarantees. Dual-write adds reconciliation risk and is explicitly out of scope.

### Decision: Preserve applied Alembic history and add only forward corrections

**Choice**: Rehearse the seven existing revisions in order on PostgreSQL 18. If a PostgreSQL incompatibility is proven, add one new revision after `2c3245f4f658`; never edit an applied revision, revision ID, or historical downgrade.

**Alternatives considered**: Rewrite SQLite-oriented revisions; create a PostgreSQL-only replacement baseline; manually create the target schema outside Alembic.

**Rationale**: Existing revision identity is part of the audit trail. A clean PostgreSQL target must be reproducible from the repository's migration history, while any correction remains reviewable and forward-only.

### Decision: Canonicalize values before checksumming, with policy-versioned manifests

**Choice**: Define a versioned canonical serializer over the six tables and stable column lists. Sort rows by primary key, encode NULL distinctly, serialize `Decimal` as fixed-point text at declared scale, and serialize timestamps only after the approved naive-timestamp interpretation is applied. Hash the canonical bytes with the approved algorithm/version. Store policy identifiers in the manifest.

**Alternatives considered**: Hash database dumps; compare driver-specific string output; use unordered row hashes; normalize timestamps implicitly.

**Rationale**: SQLite and PostgreSQL drivers return different representations for timestamps, numerics, and NULLs. Canonical serialization makes parity meaningful and prevents an unapproved timezone conversion from being hidden by a checksum.

### Decision: Make cutover operational and non-destructive

**Choice**: Freeze source writes, export and validate, point the application at PostgreSQL only after all gates pass, and retain source/target evidence. If a pre-acceptance gate fails, stop target writes and route back to the unchanged SQLite snapshot only under the documented operational procedure; do not downgrade Alembic or delete target evidence.

**Alternatives considered**: Destructive database downgrade; automatic rollback by deleting target rows; dual-write until confidence is established.

**Rationale**: Historical movement and sale data are append-only. Preserving both datasets supports diagnosis and reconciliation, while destructive rollback would destroy audit evidence. PostgreSQL becomes the sole application database only after acceptance.

## Data Flow

```text
DATABASE_URL ──→ Settings validation ──→ SQLAlchemy engine / Alembic
                                      └─→ safe redacted diagnostics

nexus.db (read-only)
    │ identify path/size/hash/revision
    │ require approved freeze
    ▼
canonical exporter ──→ versioned export + source manifest
                              │ verify source identity/policy
                              ▼
clean PostgreSQL 18 ── Alembic head ──→ ordered importer
                              │ usuarios → productos → proveedores
                              │ → movimientos_inventario → ventas → venta_items
                              ▼
sequence repair ──→ parity/FK/append-only/concurrency checks
                              ▼
credential-free manifest ──→ acceptance gate ──→ cutover or preserved rollback
```

The load order is intentionally the specified order even where some tables are independent: `usuarios`, `productos`, `proveedores`, `movimientos_inventario`, `ventas`, `venta_items`. Each table is represented in the export and manifest even when its count is zero. Imported primary keys are explicit; after each table load, its PostgreSQL sequence is set to at least `MAX(id)` (or a valid initial state for an empty table), and a next-ID insert check proves non-collision.

## Interfaces / Contracts

The exact public CLI name can be finalized during tasks, but the implementation should expose stable library contracts so tests do not shell out to a live database for unit coverage:

```python
TABLE_ORDER: tuple[str, ...] = (
    "usuarios",
    "productos",
    "proveedores",
    "movimientos_inventario",
    "ventas",
    "venta_items",
)

@dataclass(frozen=True)
class SnapshotIdentity:
    path: str
    size_bytes: int
    sha256: str
    alembic_revision: str
    identified_at: str

@dataclass(frozen=True)
class MigrationPolicy:
    format_version: str
    checksum_algorithm: str
    timezone_policy: str
    decimal_policy: str
    canonical_columns: dict[str, tuple[str, ...]]

def identify_source(path: Path) -> SnapshotIdentity: ...
def export_snapshot(source: Path, destination: Path, *, freeze_token: str,
                    policy: MigrationPolicy) -> ExportManifest: ...
def import_snapshot(export: Path, target: Connection,
                    policy: MigrationPolicy) -> ImportResult: ...
def validate_parity(export: ExportManifest, target: Connection,
                    policy: MigrationPolicy) -> ValidationResult: ...
```

The CLI must accept explicit source/export/manifest paths and a dry-run mode. It must never accept a credential-bearing URL as a positional value that is persisted in evidence, and all diagnostics must redact userinfo. The freeze token is an explicit operator-controlled input; absence or mismatch prevents an authoritative export. The export format should be a versioned JSON-lines or equivalent controlled format with UTF-8, stable key/column order, explicit NULL markers, and no plaintext password material beyond the existing opaque `password_hash` field.

The manifest contract includes: format and policy versions; source path, byte size, hash, Alembic revision, and export time; target server/schema/revision identity without credentials; per-table source/target counts and checksums; FK/orphan results; timestamp and Decimal policies; maximum IDs and post-repair sequence values; next-ID results; append-only before/after fingerprints; every check outcome; and an overall `accepted: false` until all gates pass. Failure entries identify table/check scope and safe remediation text.

## File Changes

| File | Action | Description |
|---|---|---|
| `app/config.py` | Modify | Require PostgreSQL URLs in all environments; centralize scheme validation and safe diagnostics. |
| `app/database.py` | Modify | Remove SQLite connection arguments/fallback behavior and construct only the validated PostgreSQL engine. |
| `alembic.ini` | Modify | Remove the usable SQLite URL; retain only non-secret Alembic script/log configuration. |
| `alembic/env.py` | Modify | Inject and validate the environment URL for online and offline modes before engine/rendering. |
| `alembic/versions/*.py` | Verify; modify only if evidenced | Audit all revisions; add a forward-only PostgreSQL correction after `2c3245f4f658` only if rehearsal proves one is needed. |
| `app/models/*.py` | Verify; modify only if evidenced | Confirm PostgreSQL metadata, numeric precision, timezone declarations, FK restrictions, and append-only constraints match migrations. |
| `scripts/migrate_sqlite_to_postgres.py` or `app/migration/` | Create | Thin CLI/composition layer for dry run, freeze gate, ordered export/import, validation, sequence repair, and manifest output. |
| `app/migration/` modules | Create | Pure canonicalization, source identity, row mapping, policy, manifest, and orchestration contracts; keep database writes isolated. |
| `tests/test_postgresql_config.py` | Create/modify | RED tests for URL schemes, missing values, redaction, and no SQLite file creation. |
| `tests/test_alembic_postgresql_only.py` | Create | RED tests for online/offline rejection and environment URL injection; integration test full head on PostgreSQL 18. |
| `tests/test_migration_*.py` | Create | Deterministic export, source immutability, ordering, NULL/Decimal/timestamp/hash preservation, manifest, FK, failure atomicity, and sequence tests. |
| `tests/conftest.py` and database tests | Modify | Add disposable PostgreSQL fixtures and isolate/review existing in-memory SQLite fixtures according to the approved test-only policy. |
| `.github/workflows/ci.yml` | Modify | Provision PostgreSQL 18, apply Alembic, run backend migration/integration checks, and remove SQLite database provisioning. |
| `requirements*.txt` | Modify only if already-pinned driver is absent | Use the existing PostgreSQL SQLAlchemy driver if present; ask before adding a dependency. |
| `.env.example`, `README.md`, `docs/migration-runbook.md` | Create/modify | Document local URL injection, dry run, freeze, cutover, validation, rollback, archive retention, and credential redaction. |
| `nexus.db` and generated evidence archive | Preserve | Do not edit or delete the source snapshot; mark evidence read-only after rehearsal/cutover. |

## Testing Strategy

The project configuration has `strict_tdd: false` and `apply.tdd: false` because backend and frontend have independent commands. This design nevertheless uses Standard TDD (RED → GREEN → REFACTOR) for every new migration/configuration behavior, while retaining the project-level commands and not claiming a workspace-wide TDD gate.

| Project/layer | RED coverage | GREEN/verification |
|---|---|---|
| Backend unit | URL scheme validation, safe error redaction, canonical serialization, stable row order, NULL/Decimal/timestamp policy, source identity drift, freeze requirement, manifest schema, and sequence SQL generation. | `pytest -v` focused tests, then complete `pytest -v`; `ruff check .`, `ruff format .`, and `mypy app`. |
| Backend PostgreSQL integration | Clean Alembic chain on PostgreSQL 18; all six tables; parent-first import; preserved IDs/FKs/hashes/timestamps/Decimal values; rollback transaction; sequence next-ID checks; zero-row sales tables. | Disposable local/CI PostgreSQL 18 only; `alembic upgrade head`; migration rehearsal and parity manifest inspection. |
| Backend PostgreSQL concurrency | Concurrent sale attempts against the existing `select_for_update`/stock semantics; historical movement/sale rows are never updated/deleted. | Run only against disposable PostgreSQL 18; SQLite results are not accepted as concurrency evidence. |
| CI/process | CI fails on a SQLite URL, reaches Alembic head, runs migration checks against the PostgreSQL service, and credential scans find no secrets. | GitHub Actions service health check, environment-injected URL, fixed commands, artifact upload of redacted manifests only. |
| Frontend project | No frontend behavior is changed by this design; run existing `npm run test` as regression protection. | `npm run test --prefix frontend` and `npm run build --prefix frontend` per config. |

Fixtures must distinguish imported source rows from generated test rows. The migration fixture source is a checked-in minimal SQLite snapshot fixture or a generated temporary copy, never production data; the target is disposable PostgreSQL. Tests must assert the source file hash before and after. Any existing SQLite unit fixture may remain only after the pending policy is approved and must never be used as runtime, Alembic, CI, parity, or concurrency evidence.

## Threat Matrix

This change touches CI command execution and a migration CLI boundary, but it does not automate Git, commits, pushes, or pull requests. The matrix is included to make those non-applicable boundaries explicit:

| Boundary | Applicability | Design response | Planned RED tests / safe failure |
|---|---|---|---|
| Documentation-like paths | N/A: no documentation file is executable and no path is classified as a command. | Run only the fixed Python entrypoint; documentation contains descriptive commands only. | No RED test; credential scan and CLI smoke test cover artifact separation. |
| Git repository selection | N/A: migration never invokes Git or selects a repository. | Source and export paths are explicit filesystem paths; reject missing or changed source identity. | No RED test; source identity drift test fails before import. |
| Commit state | N/A: migration does not stage or commit files. | Evidence is written to an explicit output path, never to Git automation. | No RED test. |
| Push state | N/A: migration does not push or resolve branches. | CI uploads only redacted evidence through its fixed workflow step if configured. | No RED test. |
| PR commands | N/A: no PR command or composed VCS command is used. | Keep review/approval outside the migration utility. | No RED test. |

Safe behavior is refusal before source mutation or target acceptance whenever paths, freeze state, URL scheme, policy, or credentials are invalid. Failure behavior is a non-accepted manifest with scoped diagnostics, no secret-bearing output, no partial cutover, and preserved source/target evidence.

## Migration / Rollout

### Phase 0 — decisions and audit

Resolve database/schema/role and secret delivery ownership, naive timestamp interpretation, canonical format/checksum version, test-only SQLite policy, write-freeze owner/downtime, non-application tables, archive retention/access, and PostgreSQL 18 rehearsal target. Audit all SQLite tables and the seven Alembic revisions. Do not connect to production or discover credentials.

### Phase 1 — PostgreSQL-only seams

Implement and test settings validation, engine construction, Alembic injection, and CI PostgreSQL 18 service provisioning. Run the full existing backend suite against the disposable PostgreSQL database before importing data. Preserve all migration revision identities.

### Phase 2 — deterministic rehearsal

Copy the approved source snapshot to a local working input only if needed; identify the original and verify its hash. Run dry-run export, inspect the manifest, require the freeze marker for the authoritative export, apply Alembic to a clean PostgreSQL 18 database, import in the fixed order, repair sequences, and validate all gates. Repeat from a clean target to prove determinism.

### Phase 3 — authorized cutover

Apply the runbook only with explicit owner approval: stop writes, verify source identity, export, validate, import/validate target, switch `DATABASE_URL`, and smoke-test the application. PostgreSQL is recorded as sole authority only after all gates pass. Keep `nexus.db`, exports, manifests, and logs read-only under approved controls.

### Rollback

Before acceptance, stop target writes, preserve the target database and evidence, and route the application back to the unchanged SQLite snapshot only through the runbook. Never delete target rows or downgrade Alembic. Capture any target writes as append-only reconciliation evidence before retrying. After acceptance, rollback means operational incident handling and reconciliation; SQLite remains archive evidence, not an ongoing runtime fallback.

### Archive

Archive the source snapshot identity, canonical export, redacted manifests, validation logs, target backup/evidence, and approval record with immutable/read-only permissions. Retention and access duration are policy gates, not implementation guesses. The OpenSpec change itself is archived only after implementation and verification, preserving the complete change history.

## Open Questions

- [ ] Which PostgreSQL database name, role, schema, and approved secret mechanism will be used for local rehearsal and CI?
- [ ] How should existing naive SQLite timestamps be interpreted, and what timezone normalization is authoritative?
- [ ] Which export format, canonical column lists, checksum algorithm/version, and manifest schema version are approved?
- [ ] Is SQLite permitted for isolated non-database unit tests, or must every database-dependent fixture use PostgreSQL?
- [ ] Who owns the write freeze, what signal/token proves it, and what downtime is acceptable?
- [ ] Which non-application SQLite tables, if any, are intentionally excluded after the complete schema audit?
- [ ] What archive retention period, access control, and target-write reconciliation procedure are required?

## Standard TDD Work Order

1. Write RED tests for PostgreSQL URL validation and safe diagnostics; implement the composition seam; refactor without reintroducing SQLite branches.
2. Write RED tests for Alembic environment injection/rejection and clean PostgreSQL head; implement the environment boundary; preserve revisions.
3. Write RED tests for source identity, freeze gating, canonical serialization, and deterministic export; implement pure migration primitives.
4. Write RED integration tests for ordered import, exact value preservation, FK failure atomicity, sequence repair, and manifest completeness; implement the importer and validator.
5. Write RED cutover/rollback/archive and concurrency tests; implement runbook/documentation and CI gates.
6. Run backend and frontend project commands, inspect redacted evidence, and perform a final no-production/no-credentials review before verification.
