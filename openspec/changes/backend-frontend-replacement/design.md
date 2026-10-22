# Design: Incremental Backend and Frontend Replacement

## Technical Approach

Implement the replacement as a sequence of independently deployable slices inside the existing repository. The current `/api/v1` FastAPI façade, response shapes, status/error semantics, authentication behavior, and existing database tables remain the compatibility boundary. Internally, the backend moves incrementally from `routers/ -> services/ -> models/` toward a modular monolith with HTTP interfaces, application use cases, domain policies, persistence/security/configuration adapters, and explicit composition wiring. The frontend moves incrementally from resource/page folders toward feature modules with shared API and UI seams, without introducing a global state library or client persistence.

The initial implementation scope is the baseline and safety-seam work described by `replacement-baseline` and `replacement-safety-seams`; later capability replacement and the sales UI are separate cuts. No schema rewrite or business-contract change is implied. The existing `movimientos_inventario`, `ventas`, and `venta_items` records remain historical evidence and are never edited or deleted.

## Architecture Decisions

### Decision: Preserve the existing API façade while replacing internals

**Choice**: Keep `app/main.py` and the `/api/v1` route registrations as the stable HTTP entry point. Introduce compatibility presenters/adapters at the interface boundary so old response fields, normalization, status codes, error vocabulary, and authentication requirements remain unchanged while use cases are migrated one capability at a time.

**Alternatives considered**: Versioning a new API immediately; changing frontend and backend simultaneously; replacing the routers with a new gateway in one release.

**Rationale**: The current frontend consumes the existing API, the proposal requires reversible strangler cuts, and the repository already has documented specs 001–013 plus the later sales contract. A stable façade prevents a flag-day consumer migration and makes parity measurable.

### Decision: Use a modular monolith with hexagonal seams, not new deployable services

**Choice**: Keep one deployable backend and define dependency direction as HTTP interfaces -> application -> domain ports, with adapters implementing persistence, security, configuration, and observability ports. Compose concrete dependencies from `app/main.py` through a dedicated composition seam.

**Alternatives considered**: Microservices; a greenfield rewrite in a new framework; retaining unrestricted router-to-ORM access.

**Rationale**: The current repository is a single FastAPI application and historical transactions require one authoritative consistency boundary. A modular monolith provides replaceable internals and clear seams without distributed transactions, operational duplication, or premature framework/ORM decisions.

### Decision: Make transaction ownership explicit at the application use-case boundary

**Choice**: A request-scoped unit of work owns one session and one commit/rollback decision for each mutating use case. Repositories and domain services do not commit independently. The sale operation owns the transaction that creates `Venta`, `VentaItem`, and linked exit movements; the canonical stock/movement operation is shared rather than duplicated.

**Alternatives considered**: Continue committing inside each existing service; one transaction per repository call; dual independent sale and movement implementations.

**Rationale**: `app/database.py` currently exposes `get_db`, while existing services commit internally. `app/services/venta_service.py` also directly instantiates `MovimientoInventario` despite its documented relationship to movement logic. Explicit ownership is required to prove atomicity, prevent partial sales, and make the discrepancy testable before sales cutover.

### Decision: Treat the existing schema as the initial source of truth

**Choice**: Repositories first map the existing SQLAlchemy models and tables under `app/models/` and the seven applied Alembic revisions under `alembic/versions/`. Any future schema change is additive, forward-only, reviewed, rehearsed, and represented by a new migration.

**Alternatives considered**: Recreate tables under new names; destructive downgrade/rebuild; backfill and switch before shadow comparison.

**Rationale**: `movimientos_inventario`, `ventas`, and `venta_items` carry immutable traceability. Preserving identifiers, timestamps, foreign keys, quantities, prices, totals, and movement links minimizes migration risk and supports rollback without rewriting evidence.

### Decision: Keep configuration and security behind validated adapters

**Choice**: Introduce providers around the current database and JWT/password configuration, with environment validation at composition time. Preserve Bearer/JWT behavior and the current auth-before-database access guarantee. Development may continue using SQLite only where the existing tests require it; production and migration/concurrency evidence must use the explicitly approved database configuration.

**Alternatives considered**: Hard-code a new production URL; silently switch all environments to PostgreSQL; add refresh tokens, roles, revocation, or rate limiting in this replacement.

**Rationale**: `app/database.py` currently hardcodes `sqlite:///nexus.db` while documentation describes environment-driven PostgreSQL. Configuration is therefore a safety seam, but new auth capabilities are out of scope and could change the contract.

### Decision: Organize the frontend by features while retaining JavaScript and in-memory server state

**Choice**: Gradually move routing/session/layout responsibilities into `frontend/src/app/`, business slices into `frontend/src/features/{catalog,suppliers,inventory,sales}/`, and shared HTTP/UI behavior into `frontend/src/shared/{api,ui}/`. Keep React 18, Vite, JavaScript ES2022, React Router, native `fetch`, and revalidation after mutations.

**Alternatives considered**: Immediate TypeScript migration; Redux or another global state library; client-side persistence/cache; a simultaneous route rewrite.

**Rationale**: The current frontend already centralizes HTTP in `frontend/src/api/client.js`, uses in-memory auth in `frontend/src/context/AuthContext.jsx`, and repeats loading/error/empty orchestration in pages. Feature seams reduce duplication without introducing unapproved dependencies or stale server data.

### Decision: Quality commands are made reproducible before changing workflow policy

**Choice**: Record and repair invocation drift as a dedicated tooling slice. Backend evidence uses the CI-equivalent `PYTHONPATH=. pytest -v` until the import layout is intentionally corrected; frontend evidence uses `npm run test` and `npm run build` from `frontend`. Replace placeholder frontend `lint`/`format` scripts only through an approved dependency/workflow change. Do not change `strict_tdd` or `openspec/config.yaml` in this design.

**Alternatives considered**: Claiming root `pytest -v` is already reproducible; enabling strict cross-project TDD immediately; adding tooling dependencies opportunistically.

**Rationale**: The current `openspec/config.yaml` has two independent projects and no workspace test command. Exploration recorded root `pytest -q` import failure and frontend placeholder scripts, while `.github/workflows/ci.yml` runs backend with `PYTHONPATH=.` and omits frontend lint/format. Evidence must reflect reality before policy changes.

## Data Flow

### Backend request and transaction flow

```text
HTTP request
    -> app/main.py route registration
    -> interfaces/http router + auth dependency + Pydantic schema
    -> application use case
    -> domain policy / invariant checks
    -> unit of work (one SQLAlchemy session)
    -> persistence repository adapters -> existing tables
    -> commit or rollback owned by use case
    -> compatibility presenter -> existing response/status/error contract
```

Reads may initially use an adapter around the existing services, then move capability by capability. Mutations must not expose a commit decision below the use-case boundary. A sale must atomically persist its sale header, items, and linked inventory exits; a failed validation or persistence operation produces no accepted partial sale.

### Frontend request and state flow

```text
Router/session boundary
    -> feature page/use case hook
    -> shared API client and resource gateway
    -> /api/v1 compatibility façade
    -> normalized response or typed error taxonomy
    -> feature state
    -> shared Loading/Error/Empty/Form/Table UI
```

Server data remains in memory. A successful mutation closes its modal/dialog, shows the existing success state, and revalidates the relevant GET. An unauthorized response goes through the existing `setOnUnauthorized` path and returns to the login boundary without leaking protected data.

### Capability cutover flow

```text
known-good implementation
        \                         +------------------+
         -> capability switch --->| old or new path  |--> response
                                  +------------------+
                                      |
                         shadow comparison / metrics
                                      |
                            cutover or route back
```

Shadow reads compare contract-level results before writes move. Dual writes are prohibited until idempotency, failure handling, reconciliation, and a stop condition have been separately approved and tested.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/main.py` | Modify incrementally | Remain composition root and stable `/api/v1` façade; wire dependencies and capability switches without embedding business logic. |
| `app/database.py` | Modify | Extract validated database configuration and explicit session/unit-of-work lifecycle while preserving test compatibility and existing engine behavior until approved. |
| `app/routers/*.py` | Modify incrementally | Keep HTTP validation and compatibility presentation; remove direct ORM/business work from routers, especially `app/routers/ventas.py`. |
| `app/services/*.py` | Modify incrementally | Preserve public behavior during characterization; delegate to application/domain operations and eliminate competing sale/movement transaction paths. |
| `app/models/*.py` | Protect initially | Continue mapping existing tables and historical relationships; no destructive or in-place historical edits. |
| `alembic/versions/*.py` | Protect | Treat current revisions as applied history; create a new revision only for an approved additive schema change. |
| `app/interfaces/http/` | Create later | HTTP-facing request mapping, response presenters, auth dependencies, and compatibility adapters. |
| `app/application/` | Create later | Capability use cases and explicit unit-of-work coordination. |
| `app/domain/` | Create later | Stock/sale policies, immutable historical concepts, domain errors, and ports independent of FastAPI/SQLAlchemy. |
| `app/adapters/persistence/` | Create later | SQLAlchemy repositories and transaction adapter over existing tables. |
| `app/adapters/security/` | Create later | JWT/password provider adapters preserving current auth semantics. |
| `app/adapters/config/` | Create later | Environment-backed validated configuration providers. |
| `app/composition/` | Create later | Dependency graph and capability routing construction used by `app/main.py`. |
| `frontend/src/App.jsx` | Modify incrementally | Keep public routes while delegating route composition to the app boundary. |
| `frontend/src/context/AuthContext.jsx` | Modify incrementally | Preserve in-memory session behavior and unauthorized handling while moving shared session concerns under `frontend/src/app/`. |
| `frontend/src/api/client.js` and `frontend/src/api/*.js` | Modify incrementally | Preserve current gateways initially, then move to `frontend/src/shared/api/` with one error/auth contract. |
| `frontend/src/pages/*.jsx` and `frontend/src/hooks/*.js` | Modify incrementally | Move orchestration into feature folders without changing route behavior or API semantics. |
| `frontend/src/components/*.jsx` | Modify incrementally | Consolidate reusable loading, error, empty, table, modal, and form states under `frontend/src/shared/ui/` where duplication is proven. |
| `frontend/src/app/`, `frontend/src/features/`, `frontend/src/shared/` | Create incrementally | Feature-oriented frontend seams for routing, catalog, suppliers, inventory, sales, API, and UI. |
| `frontend/package.json` | Modify in tooling slice | Replace placeholder quality scripts only after dependency/workflow approval; do not add dependencies in this design. |
| `.github/workflows/ci.yml` | Modify in tooling slice | Align local and CI commands, add approved contract/integration evidence, and keep backend/frontend jobs independently diagnosable. |
| `tests/` | Add/modify | Characterization, contract, security, transaction, append-only, migration, and rollback-signal tests; existing behavior tests remain regression gates. |
| `frontend/src/**/*.test.*` | Add/modify | Feature boundary, API error, auth redirect, revalidation, accessibility, and route compatibility tests. |
| `openspec/changes/backend-frontend-replacement/design.md` | Create | This technical design; no production code is implemented by this phase. |

## Interfaces / Contracts

### Backend application ports

The exact Python names may be finalized in tasks, but the dependency shape should be equivalent to:

```python
class UnitOfWork(Protocol):
    productos: ProductRepository
    proveedores: SupplierRepository
    movimientos: MovementRepository
    ventas: SaleRepository

    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, exc_type, exc, traceback) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class RegisterSale(Protocol):
    def execute(self, command: RegisterSaleCommand) -> SaleResult: ...
```

The concrete SQLAlchemy implementation may use the existing `Session` internally, but repositories must not call `commit()` or `rollback()` on their own. Domain/application results are mapped to the currently documented response schemas. Domain errors are translated once at the HTTP boundary to the existing status/error vocabulary.

### Compatibility contract

Each migrated capability must have a ledger entry containing method/path, auth requirement, request schema, normalization, response fields, status codes, error bodies, and representative fixtures. The adapter must preserve `/api/v1` paths and current client assumptions. A deviation is recorded as a deviation/open decision, not silently normalized into a new requirement.

### Historical data contract

- `movimientos_inventario`, `ventas`, and `venta_items` are append-only evidence.
- Existing IDs, timestamps, quantities, prices, totals, foreign keys, and sale-to-movement links must remain readable and unchanged.
- Stock remains derived from initial stock plus entries minus exits; recalculation is verification, not silent repair.
- Any additive migration requires an Alembic revision, upgrade rehearsal, counts/checksums, and a reconciliation outcome.

### Frontend shared API contract

The shared client must preserve the behavior currently centralized by `frontend/src/api/client.js`: base URL from environment, auth token injection, unauthorized callback, JSON parsing, and a distinguishable connection/validation error taxonomy. Resource gateways keep one module per resource and components never call `fetch` directly.

## Testing Strategy

The project has two separately testable projects, so SDD+TDD evidence is recorded per project. `strict_tdd` remains false because there is no approved workspace command; every implementation task nevertheless starts with a failing test in the affected project, then implementation, then refactor.

| Layer | Backend (`.`) | Frontend (`frontend`) | Evidence |
|------|----------------|------------------------|----------|
| Unit / RED | Domain stock/sale invariants, normalization, error mapping, configuration validation, unit-of-work ownership. | Shared error taxonomy, route guards, feature selectors/hooks, defensive row validation, UI state transitions. | Test is committed or included in the task before production change. |
| Contract / integration | `/api/v1` method/path/auth/status/schema fixtures; router-to-use-case wiring; auth-before-DB; repository mappings. | API gateway paths/payloads, unauthorized redirect, revalidation after mutation, route compatibility. | Compare against the ledger and existing specs 001–014. |
| Transaction / data safety | Sale atomicity, movement linkage, rollback on failure, append-only protections, stock serialization, migration upgrade/checksums. | No client persistence; failed mutation preserves form/error state; successful mutation re-fetches server data. | SQLite for fast tests where valid; approved PostgreSQL run for locking/concurrency evidence. |
| E2E / smoke | Authenticated API smoke flows for catalog, suppliers, movements, stock, and sales once each slice is available. | Browser smoke for protected routes and later `/ventas`/`/ventas/historial`; use the real API in an approved local environment. | Run before capability cutover, not as a substitute for unit/contract tests. |
| Regression | Existing `tests/` suite, especially `test_venta_atomicidad_T05_012.py`, `test_ventas_post_T06_012.py`, `test_integracion_movimientos_T13.py`, and auth/protection tests. | Existing Vitest and structure/router tests, including `frontend/src/App.test.jsx`, `Login.test.jsx`, and `ProtectedRoute.test.jsx`. | No existing behavior is removed without an approved delta spec. |

### Required command evidence

- Backend: `PYTHONPATH=. pytest -v`, `pytest --cov=app --cov-report=term-missing`, `ruff check .`, `ruff format --check .`, and `mypy app` with the repository's current environment assumptions documented.
- Frontend: `npm run test` and `npm run build` from `frontend`; `npm run lint` and `npm run format` must not be reported as meaningful quality gates while they remain placeholders.
- CI: preserve the separate jobs in `.github/workflows/ci.yml` until an approved workspace command exists. Report warnings (including React `act(...)` warnings) separately from pass/fail.

## Threat Matrix

Routing and process-integration boundaries apply because the design introduces capability-level application/deployment routing switches and changes executable quality-command composition. VCS/PR automation is not introduced.

| Boundary | Applicability | Design response | Expected safe behavior | Expected failure behavior | Planned RED tests |
|---|---|---|---|---|---|
| Documentation-like paths | N/A — the replacement does not classify or execute documentation-like files. | No executable treatment for `requirements.txt`, Markdown, or `README.sh`. | Documentation remains data/artifact content only. | No command may infer execution from a documentation filename. | None required. |
| Git repository selection | N/A — no Git selector or repository discovery command is added. | CI/workflow paths remain repository-configured; no `git -C` composition. | Tests run in the checked-out repository. | Repository selection is not accepted as runtime input. | None required. |
| Commit state | N/A — no commit automation is designed. | Changes are reviewed through the existing workflow; implementation tasks do not stage/commit. | No production behavior depends on index state. | No code path attempts to commit or infer staged content. | None required. |
| Push state | N/A — no push, tracking branch, or refspec automation is designed. | Deployment/cutover authorization remains external to this change. | Capability switch changes only in an approved deployment process. | No local command pushes or selects a remote destination. | None required. |
| PR commands | N/A — no PR creation/update or composed PR command is designed. | Review remains governed by the 400-line policy and normal repository tooling. | Artifacts are reviewable without invoking a PR API. | No untrusted input is composed into a PR command. | None required. |
| Capability/application routing | Applicable — old/new capability paths and rollback switches are part of the design. | Use an allowlisted capability key, explicit default-to-known-good behavior, and observable route decision. | Missing/invalid switch routes to the last known-good implementation; no partial request fan-out. | New path is not selected when parity, auth, transaction, or invariant checks fail; cutover stops and routes back. | RED tests for invalid switch fallback, old/new response parity, auth parity, transaction failure fallback, and rollback after invariant/history mismatch. |
| Shell/quality command integration | Applicable — CI and local command alignment is a delivery boundary. | Keep commands as fixed configuration, use explicit working directories, and report unavailable placeholder scripts honestly. | Backend and frontend commands execute only in their intended project roots. | A failed command fails its job and does not silently become a pass; no shell input is interpolated from request data. | RED tests/checks for backend cwd/import behavior, frontend cwd, failed lint/format signaling after replacement, and independent job failure propagation. |

## Migration / Rollout

### Phase 0 — baseline and ledger

1. Freeze an evidence snapshot of OpenAPI, representative authenticated/unauthenticated fixtures, schemas, error bodies, normalization, migration heads, table counts, historical links, stock formula, and current test/CI commands.
2. Classify each entry as documented contract, observed behavior, deviation, assumption, dependency, or open decision.
3. Establish CI-equivalent commands without changing product behavior, then review the ledger as the release gate for every later slice.

### Phase 1 — safety seams

1. Add environment-backed configuration validation and preserve current development test setup.
2. Characterize router/service behavior and extract explicit dependency and unit-of-work boundaries.
3. Add auth-before-DB, Bearer/expiry, compatibility, append-only, sale atomicity, and observability regression coverage.
4. Do not route traffic to new internals until RED-GREEN-REFACTOR evidence and ledger parity exist.

### Phase 2+ — bounded strangler cuts

1. Route a low-risk read capability through the new application seam while the old path remains deployable.
2. Compare shadow reads and contract fixtures; cut over only when parity and operational signals are acceptable.
3. Migrate catalog/supplier/inventory operations in bounded slices.
4. Migrate sales only after the authoritative transaction operation proves sale-item/movement atomicity and traceability under approved database/concurrency tests.
5. Restructure frontend foundations, then feature modules, then the separately specified sales UI. Each is independently tested and reversible.

### Data migration and rollback

No destructive data migration is authorized. If new tables/columns become necessary, use a new forward-only Alembic revision, rehearsal, backup, preserved identifiers/timestamps, counts/checksums, and explicit mismatch reconciliation. Shadow reads precede any dual-write proposal.

Rollback is an application/deployment action: disable the new capability switch, stop writes to an incompatible target, route to the last known-good implementation, preserve logs and accepted writes, and reconcile through append-only evidence. A rollback must not downgrade or rewrite historical tables. Completion requires restored contract checks, stock/history invariant checks, and a documented reconciliation/incident record.

## Open Questions

- [ ] Is PostgreSQL mandatory for migration rehearsal and concurrency verification, or is SQLite acceptable for any specific slice beyond fast unit tests?
- [ ] Is compatibility required for undocumented client behavior in addition to the documented `/api/v1` contracts?
- [ ] Will the target backend remain FastAPI/SQLAlchemy, or is a framework/ORM decision required before creating the adapter interfaces?
- [ ] Should the frontend remain JavaScript ES2022 for the entire program, or should TypeScript be a separately approved migration?
- [ ] Which deployment mechanism will provide the allowlisted capability switch and last-known-good routing control?
- [ ] What approved workspace command, if any, will eventually allow `strict_tdd` and cross-project verification to change?
- [ ] Which observability sink and retention policy are available for cutover metrics, audit evidence, and rollback reconciliation?
