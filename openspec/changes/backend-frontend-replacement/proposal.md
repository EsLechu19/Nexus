# Proposal: Incremental Backend and Frontend Replacement

## Intent

Nexus needs a coherent replacement and restructuring of its FastAPI/SQLAlchemy backend and React/Vite frontend without a flag-day rewrite. The initiative will reduce boundary drift, establish an evidence-based compatibility baseline, and enable independently verifiable replacement slices while preserving the existing API contracts, historical inventory and sales evidence, traceability, and application-level rollback.

The first delivery is deliberately limited to a baseline/contract ledger and safety seams. Later phases will replace bounded backend capabilities, reorganize the frontend by feature, implement the already specified sales frontend, and perform controlled cutover only after parity and rollback evidence exist.

## Scope

### In Scope

- **Phase 0 — Baseline and contract ledger:** inventory documented `/api/v1` routes, request/response schemas, status and error semantics, authentication behavior, database/migration history, append-only invariants, tests, CI commands, and known implementation/documentation deviations. Record facts and deviations separately from desired behavior.
- **Phase 1 — Safety seams:** establish configuration/secrets providers, explicit dependency and transaction boundaries, compatibility characterization tests, security regression coverage, observability hooks, and reproducible backend/frontend quality commands without changing product behavior or rewriting the schema.
- Define an incremental program boundary with independently verifiable cuts for backend modularization, frontend feature restructuring, later sales UI delivery, quality/CI hardening, migration rehearsal, and capability-level cutover.
- Preserve current API paths and semantics initially, including normalization, status codes, response fields, error vocabulary, authentication requirements, and documented append-only behavior. Use adapters when internal implementations change.
- Preserve `movimientos_inventario`, `ventas`, `venta_items`, and related historical relationships as immutable evidence. Any schema evolution must be additive and use forward-only Alembic migrations.
- Define rollback at the application/deployment routing layer, including traffic reversion, write-stop/reconciliation handling, monitoring signals, and evidence preservation.

### Out of Scope

- Implementing the replacement, rewriting the backend, restructuring the frontend, or changing production traffic in this proposal phase.
- A flag-day rewrite, simultaneous consumer/data switch, destructive migration, migration downgrade that removes historical facts, or editing/deleting inventory movements or sales.
- Changing stock derivation, sale atomicity, movement generation, normalization, authentication semantics, or any other business contract without an approved delta spec and characterization evidence.
- New business capabilities not already specified, including roles, reusable customers, payments, returns, reservations, multi-warehouse stock, reporting, rate limiting, or internationalization.
- Choosing the future backend framework/ORM, frontend language, PostgreSQL rehearsal requirement, undocumented-client compatibility policy, or workspace command without an explicit decision record.

## Capabilities

### New Capabilities

- `replacement-baseline`: Evidence-based API, data, test, CI, and deviation inventory represented by a maintained contract ledger before replacement work begins.
- `replacement-safety-seams`: Compatibility adapters, explicit transaction/dependency seams, security regression coverage, observability, and application-level rollback controls that allow bounded replacement without changing external behavior.

### Modified Capabilities

- None initially. Existing catalog, supplier, inventory movement, stock, authentication, sales, and frontend capabilities remain contract-compatible during the baseline and safety-seam phases. Later replacement slices must use delta specs only when requirements—not merely implementation—change.

## Approach

Treat the initiative as a sequence of changes rather than one rewrite:

1. **Baseline/contract ledger:** capture OpenAPI and representative fixtures, endpoint/auth matrices, schema and migration inventory, append-only checks, stock and sales invariants, test commands, CI behavior, and known deviations. Reconcile the local backend invocation with CI evidence without silently changing SDD configuration.
2. **Safety seams:** move configuration and secrets behind validated providers, characterize the router/service boundary, make transaction ownership explicit, add contract/security/invariant tests, and add structured operational signals. In particular, characterize the current sales/movement transaction discrepancy before consolidating it; there must be one authoritative operation for stock deduction.
3. **Backend modular monolith:** later introduce interfaces/HTTP, application use cases, domain policies, persistence adapters, security/config adapters, and composition wiring behind the existing API façade. Route one bounded capability at a time, starting with low-risk reads, then catalog/inventory, and sales only after atomicity and movement traceability are proven.
4. **Feature-oriented frontend:** later organize routing/session boundaries, shared API/error contracts, shared UI states/design tokens, and feature modules for catalog, suppliers, inventory, and sales. Preserve in-memory server data and revalidation until a separate caching decision is approved.
5. **Sales frontend:** implement `/ventas` and `/ventas/historial` only as a later, independently tested slice against the confirmed `012` backend contract and `014` frontend behavior; this proposal does not invent sales capabilities.
6. **Quality and CI:** make backend and frontend commands reproducible, replace placeholder frontend quality scripts, add integration/smoke checks and contract comparisons, and keep each implementation slice within the 400-line review budget. Do not change `strict_tdd` or OpenSpec configuration until a separate workflow decision approves it.
7. **Migration/cutover:** rehearse additive migrations, checksums/counts, PostgreSQL/concurrency verification where approved, shadow-read comparison, capability-level feature flags or deployment switches, monitoring, rollback, and only then retire superseded internals.

### Baseline and Contract Ledger

The ledger must be the release gate for every replacement slice and include, at minimum:

- route, method, authentication requirement, request/response schema, normalization, status/error semantics, and consumer ownership;
- database tables, columns, foreign keys, migration versions, historical IDs/timestamps, and append-only/update-delete protections;
- stock formula and sale atomicity/traceability invariants with representative fixtures;
- current test/lint/format/typecheck/build commands, CI equivalents, coverage evidence, and known warnings/failures;
- classification of each item as documented contract, observed behavior, deviation, assumption, dependency, or open decision.

The ledger records deviations for resolution; it does not promote accidental behavior to a desired requirement without review.

### Data Safety and Rollback

The existing tables remain the initial source of truth. New tables or columns require forward-only Alembic migrations, rehearsed backfills, checksums/counts, preserved IDs and timestamps where possible, and explicit reconciliation for mismatches. Shadow reads and comparisons precede any dual-write design; dual writes are prohibited until idempotency, failure handling, reconciliation, and a stop condition are specified.

Rollback means reverting capability routing to the last known-good application version, stopping writes to an incompatible target, reconciling accepted writes through append-only correction evidence, and preserving logs and audit data. It does not mean destructive database downgrade or rewriting historical inventory/sales records.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `openspec/changes/backend-frontend-replacement/` | New | Baseline, proposal, and later phase artifacts for the replacement program. |
| `app/main.py`, `app/routers/`, `app/services/`, `app/schemas/` | Later Modified | Preserve the HTTP façade while introducing explicit composition, application, and compatibility seams; remove ORM/business work from routers incrementally. |
| `app/models/`, `alembic/` | Protected / Later Modified | Preserve historical schema and relationships; any additive change requires a new Alembic migration and verification. |
| `frontend/src/` | Later Modified | Move toward `app/`, `features/`, `shared/api`, and `shared/ui` boundaries while preserving routes and behavior. |
| `frontend/package.json`, CI configuration | Modified later | Replace placeholder quality commands and add evidence-based cross-project checks only through an approved workflow change. |
| `specs/001-*` through `specs/014-*` | Referenced | Existing behavior contracts and the sales UI contract remain compatibility inputs; no requirements are silently rewritten. |
| `docs/constitution.md`, `openspec/config.yaml` | Protected | Existing architectural and workflow constraints remain in force; changing them requires explicit approval. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Stock corruption or partial sales during replacement | High | Invariant tests, transaction/concurrency tests, shadow comparison, PostgreSQL rehearsal where approved, and application traffic rollback. |
| Hidden API or frontend contract breakage | High | Contract ledger, OpenAPI/fixture comparison, preserved `/api/v1` façade, compatibility adapters, and authenticated integration smoke tests. |
| Divergent sales and movement implementations | High | Characterize current behavior first, define one authoritative transaction operation, and block sales cutover until atomicity and movement links are proven. |
| Irreversible or lossy data migration | High | Additive migrations only, backups, rehearsal, checksums/counts, original identifiers/timestamps, and no destructive historical downgrade. |
| Security regression at a new boundary | Medium | Preserve auth-before-DB behavior and add login, Bearer, expiry, and unauthorized-access regression tests before routing traffic. |
| False confidence from inconsistent quality commands | Medium | Record executable local/CI commands, fix invocation drift, replace frontend placeholders, and report warnings separately from pass/fail. |
| Review units become unmanageable | Medium | Split backend, frontend, sales UI, tooling, migration, and cutover into independently verifiable changes under the 400-line review policy. |

## Rollback Plan

Each capability cut must have a deployable previous version and an explicit routing switch. If contract errors, authentication failures, transaction failures, stock invariant violations, history-count mismatches, or unacceptable operational signals appear, stop the cutover and route traffic back to the last known-good implementation. Preserve all accepted writes and evidence; do not delete or downgrade historical tables. If a new persistence path received writes, disable it, reconcile using an append-only correction/reconciliation process, and require ledger parity before retrying. Rollback completion requires restored contract checks, invariant checks, and a documented incident/reconciliation record.

## Dependencies

- Approved baseline and contract-ledger format, representative fixtures, and access to CI/deployment evidence.
- Decision on whether PostgreSQL is mandatory for migration rehearsal and concurrency verification.
- Decision on compatibility scope for undocumented client behavior.
- Decision on target backend framework/ORM, frontend JavaScript versus TypeScript, and any workspace-level command; none is assumed here.
- Deployable last-known-good application versions and a capability-level routing or feature-flag mechanism before cutover work.
- Confirmation of the existing `012`/`014` sales contract before implementing the later frontend sales slice.

## Success Criteria

- [ ] A reviewed ledger covers 100% of documented `/api/v1` endpoints, auth requirements, schemas, status/error semantics, migrations, append-only invariants, and known deviations.
- [ ] Baseline backend and frontend commands are reproducible locally and in CI, with pass/fail evidence and warnings reported separately; existing product behavior is unchanged.
- [ ] Characterization tests cover representative catalog, supplier, inventory, stock, authentication, and sales flows, including append-only and sale-to-movement traceability invariants.
- [ ] Safety seams prove authentication occurs before business/database access, transaction ownership is explicit, configuration is environment-driven, and compatibility responses remain stable.
- [ ] Every later replacement slice has a bounded scope, delta/spec coverage when behavior changes, independent verification, a rollback switch, and a ledger update before cutover.
- [ ] No implementation phase edits/deletes historical inventory or sales records, rewrites applied migrations, changes stock/sale semantics implicitly, or introduces unapproved business capabilities.
- [ ] Backend modularization, feature-oriented frontend restructuring, sales frontend implementation, quality/CI hardening, migration rehearsal, and cutover are delivered as separate verifiable changes rather than a flag-day rewrite.
