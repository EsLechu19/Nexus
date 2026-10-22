# Exploration: Nexus backend and frontend replacement

## Executive summary

Nexus is a working layered FastAPI application and React/Vite client with documented contracts for products, suppliers, inventory movements, stock, authentication, and append-only sales. It is not yet a single coherent replacement target: the frontend has no sales UI, the two projects are tested independently, and several implementation/documentation boundaries already diverge from the constitutions and specs.

The safest candidate is an incremental modular-monolith replacement behind preserved API and database contracts, not a greenfield flag-day rewrite. Historical inventory movements and sales remain immutable evidence; migration must be additive, replayable, and reversible at the traffic-routing layer.

## Current state — verified facts

### Repository and SDD

- The repository contains the original SDD material in `specs/001-*` through `specs/014-frontend-ventas/`; the native OpenSpec home is `openspec/`.
- `openspec/config.yaml` detects two projects: backend at `.` and frontend at `frontend`.
- Backend and frontend have independent commands (`pytest -v` and `npm run test`) and no workspace command covering both. Therefore `strict_tdd: false` is currently justified by configuration, but this is a workflow limitation, not evidence that TDD is undesirable.
- No implementation was changed in this exploration. The worktree already contains changes/untracked files including CI, README, `.codegraph/`, `openspec/`, and `specs/014-frontend-ventas/`; these must be separated from future replacement work.

### Backend

- Entry point: `app/main.py`; routes are grouped under `/api/v1` for auth, products, suppliers, movements, stock, and sales.
- The nominal architecture is `routers/` → `services/` → SQLAlchemy `models/`, with Pydantic `schemas/` and Alembic migrations.
- The database module currently hardcodes `sqlite:///nexus.db`, while documentation/configuration describe environment-driven PostgreSQL in production. This is a configuration seam and deployment risk.
- `app/routers/ventas.py` performs ORM queries and response projection (`VentaItem`, `Producto`, movement IDs), contrary to `docs/constitution.md` §3. Similar router/service boundary conformance should be inventoried before replacement.
- `app/services/venta_service.py` documents strict reuse of movement logic, but its transaction path directly instantiates `MovimientoInventario` rather than calling the `003` service function. This is a contract/implementation discrepancy requiring explicit characterization tests before changing it.
- Historical invariants are explicit: `movimientos_inventario` and `ventas` are append-only; stock is derived from initial stock plus entries minus exits; successful sales link sale items to generated movement IDs.
- Authentication is JWT/Bearer-based and currently stateless, with accepted limitations around rate limiting, revocation, roles, and audit-by-user.

### Frontend

- Entry point: `frontend/src/App.jsx`; React Router protects the existing products, suppliers, movements, and stock routes with an in-memory auth context.
- HTTP is centralized in `frontend/src/api/client.js` and resource modules. Loading/error/empty states and post-mutation revalidation are repeated across pages.
- `specs/014-frontend-ventas/spec.md` is detailed, but the current route map has no `/ventas` or `/ventas/historial`; the sales UI is planned, not implemented.
- `frontend/package.json` has placeholder `lint` and `format` scripts and no typecheck command. CI runs frontend tests and build but not lint/format.
- The frontend test command passed in this environment: 40 files and 322 tests. It emits React `act(...)`/deprecated-act warnings that are quality debt, not failures.
- The backend command `pytest -q` failed from the repository root with `ModuleNotFoundError: app`; CI compensates with `PYTHONPATH=.`. The executable CI command and local command are therefore not equivalent.

### Quality and delivery

- CI is split into backend and frontend jobs, each with its own dependency installation and verification.
- Existing documentation claims a broader verified state than the current repository command behavior proves. The replacement initiative must establish one evidence-based baseline before declaring parity.

## Facts, assumptions, and pending decisions

### Facts

1. Existing API and persistence contracts are documented in specs 001–013 and consumed by the current frontend.
2. Inventory movements and sales are historical records and must not be edited or deleted.
3. The current native SDD configuration intentionally has `strict_tdd: false` because no cross-project test command exists.
4. Frontend sales is specified but absent from the current route tree.

### Assumptions to validate before proposal/design

1. A modular monolith remains an acceptable deployment shape while internal modules are replaced.
2. Existing API paths and response semantics should remain compatibility targets during migration unless a new approved spec supersedes them.
3. A controlled cutover can be performed with a deployable previous version available for rollback.

### Decisions still open

- Whether the target backend remains FastAPI/SQLAlchemy or changes framework/ORM; no business requirement currently forces a stack change.
- Whether compatibility is required only for current documented APIs or also for undocumented client behavior.
- Whether a real PostgreSQL environment is mandatory for migration rehearsal and concurrency verification.
- Whether to introduce roles, refresh/revocation, rate limiting, audit-by-user, pagination, or reusable customers; these are not current requirements and must not be smuggled into the replacement.
- Whether the frontend should remain JavaScript or move to TypeScript; this is a maintainability choice, not an inferred business need.
- Whether to add a workspace command that runs both projects. Until explicitly approved, do not change `strict_tdd` or the OpenSpec configuration.

## Reasonable replacement boundary

### In scope

- Backend module and dependency-boundary restructuring, API contract characterization, configuration/secrets hardening, testability, observability, and documentation.
- Frontend feature-structure and design-system cleanup, centralized API/error contracts, accessibility and quality tooling, and implementation of the already specified sales UI only after its contract is confirmed.
- Migration tooling, compatibility adapters, data checks, cutover controls, and rollback rehearsal.

### Explicitly out of scope unless separately approved

- Changing the meaning of stock calculation, sale atomicity, or append-only history.
- Editing/deleting historical inventory movements or sales, rewriting applied migrations, or silently recomputing historical totals.
- New business capabilities such as roles, customer master data, payments, returns, reservations, multi-warehouse stock, reporting, or internationalization.
- A flag-day replacement that requires all consumers and persisted data to switch simultaneously.

## Candidate target architecture

### Backend: modular monolith with hexagonal seams

- `interfaces/http`: routers, request/response schemas, authentication boundary, OpenAPI.
- `application`: use cases such as catalog management, inventory movement, stock query, sale registration, and authentication orchestration.
- `domain`: immutable historical concepts, stock policy, sale invariants, validation policies, and domain errors independent of FastAPI/SQLAlchemy.
- `adapters/persistence`: SQLAlchemy repositories and transaction unit-of-work over the existing schema first; later schema changes require Alembic migrations.
- `adapters/security` and `adapters/config`: JWT/password/configuration providers with environment validation.
- `composition`: application wiring and dependency injection in `app/main.py`.

The first target should preserve the existing API façade and database tables. Internally, it should move ORM queries out of routers and make the transaction boundary explicit. The sales use case must either call the canonical movement operation or formally replace it with one shared domain/application operation; keeping two implementations is not acceptable.

### Frontend: feature-oriented client with shared contracts

- `app/`: routing, auth/session boundary, global error handling, and layout.
- `features/catalog`, `features/suppliers`, `features/inventory`, `features/sales`: page orchestration, local state, and feature components.
- `shared/api`: one typed/validated client contract, auth handling, timeout/error taxonomy, and resource gateways.
- `shared/ui`: loading, error, empty, modal, table, form, and design tokens.
- Keep server data non-persistent and revalidated until a separate caching decision is approved.

This structure reduces the current repeated page orchestration without introducing a global state library by default. A TypeScript migration is optional and requires a separate decision.

## Migration, compatibility, and rollback strategy

1. **Baseline and characterization:** freeze the currently documented API/OpenAPI behavior, schema versions, append-only checks, auth behavior, and representative inventory/sales fixtures. Record known deviations rather than encoding them as desired behavior.
2. **Strangler seams:** introduce the target application behind the current route façade. Route one bounded capability at a time while the old capability remains deployable.
3. **Contract compatibility:** keep `/api/v1` paths, status semantics, normalization, error vocabulary, response fields, and auth requirements stable initially. Use adapters for old response shapes rather than changing clients and server together.
4. **Data safety:** use the existing tables as the initial source of truth. Add new tables/columns only through forward-only Alembic migrations; backfill with checksums/counts and never rewrite historical facts. Preserve original IDs and timestamps where technically possible.
5. **Dual verification, not blind dual writes:** if a new persistence model is required, shadow-read and compare first. Any dual-write plan must define idempotency, reconciliation, failure handling, and a stop condition before implementation.
6. **Cutover:** enable capability-level routing with an explicit feature flag or deployment switch, monitor contract errors, transaction failures, stock invariants, and history counts.
7. **Rollback:** revert routing to the last known-good implementation, stop new writes to an incompatible target, reconcile any accepted writes using an append-only correction/reconciliation process, and preserve audit evidence. Database rollback must not mean destructive downgrade of historical tables.

Rollback is therefore primarily an application/deployment rollback. Destructive database downgrade is prohibited for inventory and sales history.

## Historical data impact

- Existing `productos`, `proveedores`, `usuarios`, `movimientos_inventario`, `ventas`, and `venta_items` are compatibility-critical until a migration inventory proves otherwise.
- `movimientos_inventario` and `ventas` must remain append-only, with foreign-key relationships and sale-to-movement traceability intact.
- No migration may change historical quantities, prices, totals, movement types, IDs, or timestamps merely to fit the target model.
- Derived current stock may be recalculated for verification, but the historical event stream is the source evidence. Any detected mismatch is a migration blocker or reconciliation case, not an opportunity for silent correction.
- Historical customer data is embedded in sales today. Introducing reusable customers later must preserve the embedded snapshot and define a separate migration decision; it must not replace or delete that snapshot.

## Risks and mitigations

- **High — stock corruption during cutover:** protect with invariant tests, transaction/concurrency tests on PostgreSQL, shadow comparison, and traffic rollback.
- **High — hidden contract breakage:** generate/compare OpenAPI and representative response fixtures; preserve status/error semantics until an approved delta exists.
- **High — divergent sale/movement logic:** characterize the current discrepancy, then consolidate one authoritative operation before routing sales to the target.
- **High — irreversible data migration:** use additive Alembic migrations, backups, rehearsal, checksums, and no destructive downgrade.
- **Medium — security regression:** preserve auth-before-DB behavior, validate environment secrets, and add security regression tests before cutover.
- **Medium — frontend/backend drift:** derive client gateways from the API contract and run both project suites plus integration smoke tests.
- **Medium — false quality confidence:** fix the local backend invocation, replace frontend placeholder quality scripts, and report warnings separately from pass/fail.
- **Medium — oversized review units:** forecast implementation against the 400-line review budget and split backend, frontend, tooling, and migration work into independently verifiable slices.

## Recommended phase cuts

1. **Phase 0 — Baseline and contract ledger:** inventory endpoints, schemas, migrations, historical invariants, tests, CI, and known deviations. Establish reproducible backend/frontend commands without changing product behavior.
2. **Phase 1 — Safety seams:** configuration providers, dependency boundaries, transaction/unit-of-work characterization, security regression tests, observability, and compatibility tests. No schema rewrite.
3. **Phase 2 — Backend bounded replacement:** migrate one low-risk read capability, then catalog and inventory operations, then sales only after atomicity and movement traceability are proven. Keep the old façade available.
4. **Phase 3 — Frontend foundation:** replace duplicated API/error/UI plumbing and improve accessibility/tooling while preserving routes and behavior. Keep sales UI as a separate slice based on spec 014.
5. **Phase 4 — Sales UI and end-to-end cutover:** implement `/ventas` and `/ventas/historial` against the stable sales contract, then run authenticated browser/API smoke tests and controlled capability cutover.
6. **Phase 5 — Hardening and retirement:** PostgreSQL migration rehearsal, performance/concurrency checks, documentation/operations runbooks, rollback drill, and only then removal of superseded internals.

The first proposal should cover Phases 0–1. Treat the full replacement as a program of bounded changes, not one change folder with an unreviewable rewrite.

## Recommendation

Proceed with an incremental modular-monolith replacement that preserves the existing API façade and historical database facts. Start with a contract/data baseline and boundary characterization; do not alter `strict_tdd` yet. To retain the project's SDD+TDD intent despite the current configuration, require each implementation task to provide RED-GREEN-REFACTOR evidence in its own backend or frontend project, and add a workspace command only in a later, explicitly approved workflow change.

## Ready for proposal

Yes, with the proposal limited initially to baseline, compatibility, and safety seams. The proposal should explicitly list the pending stack, compatibility, PostgreSQL, language/tooling, and workspace-command decisions; it should not assume a business rewrite or authorize source implementation yet.
