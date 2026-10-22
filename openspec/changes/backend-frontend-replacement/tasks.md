# Tasks: Incremental Backend and Frontend Replacement

This task plan implements Phase 0 (baseline/contract ledger) and Phase 1
(safety seams) first. Later work is planned as separate, reversible changes;
it is not a flag-day rewrite. Every implementation task is expected to use
RED-GREEN-REFACTOR in the affected project even though `strict_tdd` remains
false because no approved workspace command covers both projects.

## Requirement key

- **RB-1** — Complete API/frontend contract ledger.
- **RB-2** — Persistence, historical, stock, and sale-traceability baseline.
- **RB-3** — Reproducible backend/frontend quality evidence.
- **RB-4** — Baseline release gate and traceability.
- **RS-1** — Compatibility-preserving application seams.
- **RS-2** — Explicit dependency and transaction ownership.
- **RS-3** — Configuration and secret safety.
- **RS-4** — Authentication/security regression seam.
- **RS-5** — Observability and safe-operation evidence.
- **RS-6** — Additive data safety and application rollback.

## Phase 0 — Baseline and contract ledger

### T0.1 — Freeze baseline scope and evidence template

- [x] T0.1 — Freeze baseline scope and evidence template
- **Objective:** Define the versioned ledger format, evidence classifications,
  baseline revision convention, and release-gate checklist before collecting
  facts.
- **Files/components:** `openspec/changes/backend-frontend-replacement/ledger/`
  (new baseline artifacts), `proposal.md`, `design.md`, specs 001–014.
- **Requirements/specs:** RB-1, RB-4; `replacement-baseline` complete contract
  ledger and release-gate requirements.
- **RED-GREEN-REFACTOR:** RED: add a validation/checklist fixture that fails
  when required ledger columns or classifications are absent. GREEN: define
  the minimum schema and valid classifications. REFACTOR: make the template
  reusable for each later capability slice.
- **Verification:** `python -m pytest -v` for the ledger validator if created;
  review the template against `spec.md` and `design.md`.
- **Done when:** The ledger template requires endpoint, data, quality,
  deviation, decision, evidence, affected slice, and rollback fields, and a
  reviewer can identify the baseline revision and release gate.
- **Dependencies:** None.
- **Risk:** Missing a field creates false parity confidence. **Rollback limit:**
  Delete only the unapproved template artifacts; do not alter application or
  historical data.

### T0.2 — Inventory documented API and frontend consumers

- [x] T0.2 — Inventory documented API and frontend consumers
- **Objective:** Record every documented `/api/v1` route and its frontend
  consumer without deciding that observed behavior is desired behavior.
- **Files/components:** `app/main.py`, `app/routers/`, `app/schemas/`,
  `frontend/src/api/`, `frontend/src/App.jsx`, relevant `specs/001-*` through
  `specs/014-*`, ledger endpoint entries.
- **Requirements/specs:** RB-1, RB-4; `replacement-baseline` endpoint and
  bounded-slice scenarios; RS-1 compatibility boundary.
- **RED-GREEN-REFACTOR:** RED: create a coverage check listing documented
  routes missing ledger entries. GREEN: add all route and consumer entries.
  REFACTOR: normalize evidence links and endpoint naming.
- **Verification:** `PYTHONPATH=. pytest -v` (backend route/schema tests);
  `npm run test --prefix frontend`; compare the ledger with OpenAPI and specs.
- **Done when:** 100% of documented routes have method, path, auth, request/
  response schema, normalization, status/error, ordering, consumer, and
  evidence fields; deviations are separately classified.
- **Dependencies:** T0.1.
- **Risk:** Hidden consumers or accidental contracts are misclassified.
  **Rollback limit:** Revert ledger-only edits; preserve both source evidence
  and deviations rather than changing endpoint behavior.

### T0.3 — Capture representative contract fixtures

- [x] T0.3 — Capture representative contract fixtures
- **Objective:** Freeze authenticated and unauthenticated request/response
  fixtures for catalog, suppliers, movements, stock, authentication, and
  sales, including error bodies and normalization.
- **Files/components:** `tests/`, `frontend/src/**/*.test.*`, ledger fixtures
  and evidence, existing API schemas.
- **Requirements/specs:** RB-1, RB-4; RS-1 response/error compatibility.
- **RED-GREEN-REFACTOR:** RED: add characterization assertions for missing
  fixtures and contract fields. GREEN: capture representative current
  behavior. REFACTOR: share fixture builders without changing production
  responses.
- **Verification:** `PYTHONPATH=. pytest -v`; `npm run test --prefix frontend`;
  inspect fixture diffs against the ledger.
- **Done when:** Each capability has representative success, validation,
  unauthorized, and not-found/conflict evidence where applicable, with source
  revision and observed/documented classification.
- **Dependencies:** T0.2.
- **Risk:** Fixture data becomes an accidental new requirement. **Rollback
  limit:** Remove only unapproved fixtures; never modify production records or
  promote deviations without a decision record.

### T0.4 — Inventory schema, migrations, and historical invariants

- [x] T0.4 — Inventory schema, migrations, and historical invariants
- **Objective:** Establish the persistence baseline for products, suppliers,
  users, movements, sales, and sale items, including immutable evidence and
  migration heads.
- **Files/components:** `app/models/`, `alembic/versions/`, `alembic.ini`,
  `tests/test_venta_atomicidad_T05_012.py`,
  `tests/test_integracion_movimientos_T13.py`, ledger data entries.
- **Requirements/specs:** RB-2, RB-4, RS-6; append-only and historical-data
  contracts in both active specs.
- **RED-GREEN-REFACTOR:** RED: add checks for missing table/relationship,
  append-only, stock-formula, and sale-to-movement evidence. GREEN: document
  current schema and make checks pass without repair writes. REFACTOR: isolate
  reusable invariant assertions.
- **Verification:** `PYTHONPATH=. pytest -v`; `alembic upgrade head` in the
  approved test database; inspect migration history and invariant output.
- **Done when:** Tables, columns, foreign keys, IDs, timestamps, migration
  revisions, stock formula, append-only protections, and traceability fixtures
  are ledgered; mismatches remain blockers/deviations, never silent fixes.
- **Dependencies:** T0.1.
- **Risk:** Test database differs from production. **Rollback limit:** No
  migration edits or downgrades; discard only temporary test data/database.

### T0.5 — Establish executable backend/frontend quality baseline

- [x] T0.5 — Establish executable backend/frontend quality baseline
- **Objective:** Record actual local and CI command results, invocation drift,
  warnings, and failures independently for both projects.
- **Files/components:** `openspec/config.yaml` (read-only), `.github/workflows/ci.yml`,
  `frontend/package.json`, ledger quality evidence.
- **Requirements/specs:** RB-3, RB-4; no workspace-command or `strict_tdd`
  change is authorized.
- **RED-GREEN-REFACTOR:** RED: add a baseline report/check that fails when a
  configured command is missing or mislabeled as passing. GREEN: record
  `PYTHONPATH=. pytest -v`, coverage, `ruff check .`, `ruff format --check .`,
  `mypy app`, frontend test/build, and current placeholder warnings. REFACTOR:
  make reports reproducible and timestamped/revisioned.
- **Verification:** Backend: `PYTHONPATH=. pytest -v`,
  `pytest --cov=app --cov-report=term-missing`, `ruff check .`,
  `ruff format --check .`, `mypy app`. Frontend: `npm run test --prefix frontend`,
  `npm run build --prefix frontend`. Do not claim frontend lint/format gates
  while scripts remain placeholders.
- **Done when:** Local/CI differences, warnings, failures, and the absence of
  a workspace command are visible; `strict_tdd` and `openspec/config.yaml` are
  unchanged.
- **Dependencies:** T0.1.
- **Risk:** A command is made green by hiding a failure. **Rollback limit:**
  Revert report/configuration-only changes; do not weaken tests or CI failure
  propagation.

### T0.6 — Approve Phase 0 release gate

- [x] T0.6 — Approve Phase 0 release gate
- **Objective:** Review and freeze the baseline revision as the prerequisite
  for safety seams and all later replacement slices.
- **Files/components:** Baseline ledger directory, review record, affected
  `proposal.md`/`design.md` references.
- **Requirements/specs:** RB-1 through RB-4.
- **RED-GREEN-REFACTOR:** RED: run the release-gate checklist with any missing
  endpoint, invariant, quality result, deviation, or rollback target marked
  blocking. GREEN: resolve evidence gaps or record explicit open items.
  REFACTOR: make the gate reusable per capability.
- **Verification:** Re-run the backend/frontend commands from T0.5 and review
  all ledger entries against the two active specs.
- **Done when:** A named baseline revision covers all required evidence, lists
  unresolved deviations/open decisions, and blocks later slices lacking
  affected ledger coverage and a last-known-good rollback target.
- **Dependencies:** T0.2–T0.5.
- **Risk:** Premature approval. **Rollback limit:** Revoke the baseline gate
  only by review record; never erase the underlying evidence.

## Phase 1 — Safety seams

### T1.1 — Add validated configuration/provider seam

- [x] T1.1 — Add validated configuration/provider seam
- **Objective:** Put database and JWT/password configuration behind validated,
  environment-driven providers while preserving test compatibility and auth
  semantics.
- **Files/components:** `app/database.py`, auth/config modules, `app/main.py`,
  environment/test fixtures, new configuration tests.
- **Requirements/specs:** RS-3; RB-4; design configuration decision.
- **RED-GREEN-REFACTOR:** RED: tests for missing/invalid configuration and
  secret non-disclosure. GREEN: provider validation at composition/startup.
  REFACTOR: centralize diagnostics and keep values out of logs/responses.
- **Verification:** `PYTHONPATH=. pytest -v`; `ruff check .`; `mypy app`;
  startup/readiness checks with valid and invalid environment values.
- **Done when:** Unsafe startup/operation fails deterministically, diagnostics
  identify the key/class without values, and existing development tests still
  use their approved database setup.
- **Dependencies:** T0.6.
- **Risk:** Environment migration changes behavior. **Rollback limit:** Keep
  the prior provider deployable and revert composition wiring only; no data or
  schema rollback.

### T1.2 — Characterize authentication-before-database behavior

- [x] T1.2 — Characterize authentication-before-database behavior
- **Objective:** Prove protected requests authenticate before business queries,
  locks, or transaction work and preserve the current Bearer contract.
- **Files/components:** `app/auth.py`, protected routers/dependencies,
  `tests/` auth/protection tests, `app/main.py` wiring.
- **Requirements/specs:** RS-4, RS-1; RB-1 fixtures.
- **RED-GREEN-REFACTOR:** RED: tests for missing/malformed Bearer, invalid
  signature, expiry, generic invalid credentials, and no DB access. GREEN:
  preserve/fix dependency ordering without changing response vocabulary.
  REFACTOR: share security fixtures and assertions.
- **Verification:** `PYTHONPATH=. pytest -v`; inspect responses/logs for no
  passwords or hashes; run existing auth tests.
- **Done when:** Valid login and token paths pass; invalid paths fail before
  business/database work; limitations around roles, revocation, refresh, and
  rate limiting remain explicit.
- **Dependencies:** T0.3, T0.6, T1.1.
- **Risk:** Auth behavior changes silently. **Rollback limit:** Route to the
  prior auth dependency; do not introduce new auth capabilities or invalidate
  existing historical data.

### T1.3 — Define explicit request dependency and unit-of-work boundary

- [x] T1.3 — Define explicit request dependency and unit-of-work boundary
- **Objective:** Characterize session ownership and make commit/rollback
  responsibility explicit without yet migrating every service.
- **Files/components:** `app/database.py`, `app/services/`, `app/routers/`,
  `app/main.py`, unit-of-work tests.
- **Requirements/specs:** RS-2, RS-1; design transaction flow.
- **RED-GREEN-REFACTOR:** RED: tests fail when repositories/services commit or
  rollback independently or when session ownership is ambiguous. GREEN: add
  the narrow boundary and adapter around current behavior. REFACTOR: document
  dependency direction and remove duplicate lifecycle decisions only within
  the characterized slice.
- **Verification:** `PYTHONPATH=. pytest -v`; `ruff check .`; `mypy app`; inspect
  transaction logs and compatibility fixtures.
- **Done when:** The affected mutation path has one visible session owner,
  one commit/rollback decision, and no product-contract change; unconverted
  paths are explicitly listed.
- **Dependencies:** T0.4, T0.6, T1.1.
- **Risk:** Partial transaction refactor creates mixed ownership. **Rollback
  limit:** Disable the seam for the affected capability and restore the last
  known-good path; do not run destructive migrations.

### T1.4 — Characterize sale atomicity and canonical movement operation

- [ ] T1.4 — Characterize sale atomicity and canonical movement operation
- **Objective:** Resolve the documented discrepancy between sale service and
  movement generation through evidence before consolidating implementation.
- **Files/components:** `app/services/venta_service.py`, movement service,
  sale/movement models and tests, ledger deviation entry.
- **Requirements/specs:** RS-2, RS-6, RB-2; sale atomicity/traceability.
- **RED-GREEN-REFACTOR:** RED: multi-item missing/inactive/insufficient-stock
  and failure-injection tests expose partial writes or divergent operations.
  GREEN: establish one authoritative operation or preserve current behavior
  behind a tested adapter. REFACTOR: remove competing transaction decisions
  only after parity is proven.
- **Verification:** `PYTHONPATH=. pytest -v`; run
  `test_venta_atomicidad_T05_012.py`, `test_ventas_post_T06_012.py`, and
  `test_integracion_movimientos_T13.py`; approved PostgreSQL concurrency test
  when the open decision permits it.
- **Done when:** Successful sales atomically persist sale/items/movements;
  failed work persists none; movement links, stock derivation, statuses, and
  diagnostics match the ledger; the discrepancy is resolved or explicitly
  blocked with evidence.
- **Dependencies:** T0.3, T0.4, T0.6, T1.3.
- **Risk:** Stock corruption or partial historical writes. **Rollback limit:**
  Stop the affected sale route and return to the last-known-good operation;
  preserve accepted writes for reconciliation and never edit/delete history.

### T1.5 — Add compatibility presenters and contract regression gates

- [x] T1.5 — Add compatibility presenters and contract regression gates
- **Objective:** Provide explicit adapters for internal response differences
  while keeping the `/api/v1` façade and consumer assumptions stable.
- **Files/components:** `app/routers/`, `app/schemas/`, new compatibility or
  presenter modules, contract fixtures, frontend API tests.
- **Requirements/specs:** RS-1, RB-1, RB-4.
- **RED-GREEN-REFACTOR:** RED: compare replacement-shaped results against
  ledger fixtures and assert path/method/status/error/field parity. GREEN: map
  internal results to existing schemas. REFACTOR: centralize one translation
  point and avoid consumer-specific forks.
- **Verification:** `PYTHONPATH=. pytest -v`; `npm run test --prefix frontend`;
  OpenAPI/fixture comparison for the affected capability.
- **Done when:** A bounded seam can be selected without changing frontend
  consumers, and the old implementation remains deployable as rollback target.
- **Dependencies:** T0.3, T0.6, T1.3.
- **Risk:** Accidental contract normalization. **Rollback limit:** Disable the
  replacement route and retain both source and observed contract evidence.

### T1.6 — Add observability, stop signals, and rollback runbook

- [x] T1.6 — Add observability, stop signals, and rollback runbook
- **Objective:** Make capability, auth, contract, transaction, invariant,
  cutover, and rollback outcomes correlatable without secrets.
- **Files/components:** application logging/metrics seam, `app/main.py`, CI or
  deployment configuration, operations/runbook artifacts, rollback tests.
- **Requirements/specs:** RS-5, RS-6, RB-4; threat matrix routing controls.
- **RED-GREEN-REFACTOR:** RED: tests/checks fail for missing capability state,
  invalid-switch fallback, secret telemetry, or absent stop condition. GREEN:
  add allowlisted switch with known-good default and structured safe signals.
  REFACTOR: keep routing/telemetry concerns separate from business logic.
- **Verification:** Backend tests; `ruff check .`; simulated invalid switch,
  contract failure, auth failure, transaction failure, stock/history mismatch;
  verify route-back and evidence preservation.
- **Done when:** Every bounded cut has measurable success/stop signals, a
  deployable previous version, and a documented application-level rollback
  that never downgrades or rewrites historical tables.
- **Dependencies:** T1.2–T1.5 and T0.6.
- **Risk:** Rollback switch is untested or telemetry leaks secrets.
  **Rollback limit:** Default all invalid/missing switches to known-good and
  stop new-target writes; reconcile append-only evidence only.

### T1.7 — Approve Phase 1 safety-seam gate

- [ ] T1.7 — Approve Phase 1 safety-seam gate
- **Objective:** Freeze evidence that Phase 1 preserves contracts and safety
  before any bounded replacement implementation begins.
- **Files/components:** ledger update, seam test reports, open-decision record,
  rollback runbook.
- **Requirements/specs:** RB-4, RS-1 through RS-6.
- **RED-GREEN-REFACTOR:** RED: evaluate missing parity, security, transaction,
  invariant, observability, or rollback evidence as blockers. GREEN: close or
  explicitly defer each item with a named decision/dependency. REFACTOR: make
  the gate reusable per later capability.
- **Verification:** Full backend suite; frontend suite; backend lint/format
  check; frontend build; review ledger parity and rollback evidence.
- **Done when:** Phase 2+ work is blocked unless it names the baseline revision,
  affected entries, preserved contracts, tests, operational signals, and
  last-known-good rollback target.
- **Dependencies:** T1.1–T1.6.
- **Risk:** Safety evidence is treated as documentation only. **Rollback
  limit:** Do not begin cutover; retain the existing implementation as sole
  route until the gate is approved.

## Later phases — explicitly separate implementation tracks

These are planned, not authorized by Phase 0–1 and must be split into separate
changes with their own specs, gates, and rollback targets.

### Phase 2 — Backend modular monolith

- [ ] B2.1 — Low-risk read seam
- **B2.1 — Low-risk read seam:** **Objective:** create
  `app/interfaces/http/`, `app/application/`, `app/domain/`,
  `app/adapters/`, and `app/composition/` behind the stable façade and route
  one read with shadow comparison. **Components:** backend modules, ledger,
  compatibility fixtures. **Requirements:** RS-1, RS-2, RS-5, RB-4. **TDD:**
  RED parity tests, GREEN adapter/use case, REFACTOR dependency direction.
  **Verify:** `PYTHONPATH=. pytest -v`, `ruff check .`, `mypy app`.
  **Done when:** response parity and route-back work. **Depends:** T1.7.
  **Risk/rollback:** internal boundary drift; disable the capability switch and
  retain the old path, with no data rollback.
- [ ] B2.2 — Catalog/supplier slices
- **B2.2 — Catalog/supplier slices:** **Objective:** migrate catalog and
  supplier capabilities one bounded slice at a time. **Components:** new
  application/domain/persistence adapters, existing routers/services, tests.
  **Requirements:** RS-1, RS-2, RB-1, RB-4. **TDD:** RED contract fixtures,
  GREEN one capability, REFACTOR shared ports only after parity. **Verify:**
  `PYTHONPATH=. pytest -v`, `ruff check .`, `mypy app`. **Done when:** each
  slice has ledger update, shadow evidence, and rollback target. **Depends:**
  B2.1. **Risk/rollback:** hidden consumer breakage; route the affected
  capability to the known-good implementation.
- [ ] B2.3 — Inventory and stock slice
- **B2.3 — Inventory and stock slice:** **Objective:** migrate movements and
  stock without changing derivation or append-only history. **Components:**
  inventory application/domain/persistence paths, invariant/concurrency tests,
  Alembic history (protected). **Requirements:** RB-2, RS-2, RS-6. **TDD:** RED
  invariant/race tests, GREEN bounded adapter, REFACTOR after approved DB
  evidence. **Verify:** `PYTHONPATH=. pytest -v`, migration checks, approved
  PostgreSQL concurrency run. **Done when:** non-negative stock, movement
  history, and rollback evidence pass. **Depends:** B2.2 and approved
  PostgreSQL decision. **Risk/rollback:** stock corruption; stop writes to the
  new path and reconcile append-only evidence, never downgrade.
- [ ] B2.4 — Sales application slice
- **B2.4 — Sales application slice:** **Objective:** migrate sales only after
  one authoritative atomic sale/movement operation is proven. **Components:**
  sale use case, repositories, compatibility presenter, sale tests. **Requirements:**
  RB-2, RB-4, RS-1, RS-2, RS-6. **TDD:** RED failure/atomicity tests, GREEN
  use-case route, REFACTOR competing transaction paths out of scope until
  proven safe. **Verify:** sale atomicity/integration suites and approved
  PostgreSQL concurrency evidence. **Done when:** sale/item/movement commit is
  atomic, traceable, parity-tested, and reversible. **Depends:** B2.3, T1.4.
  **Risk/rollback:** partial sale; immediately route to known-good and preserve
  accepted writes for reconciliation.

### Phase 3 — Frontend feature-oriented foundation

- [ ] F3.1 — App boundary
- **F3.1 — App boundary:** **Objective:** move routing/session/layout into
  `frontend/src/app/` while retaining public routes and in-memory auth.
  **Components:** `App.jsx`, `AuthContext`, layout, route tests. **Requirements:**
  RS-1, RB-4. **TDD:** RED route/auth tests, GREEN move, REFACTOR imports.
  **Verify:** `npm run test --prefix frontend`, `npm run build --prefix frontend`.
  **Done when:** all existing routes and unauthorized redirects pass. **Depends:**
  T1.7. **Risk/rollback:** route breakage; restore prior route composition.
- [ ] F3.2 — Shared API/UI seams
- **F3.2 — Shared API/UI seams:** **Objective:** centralize API/error/auth
  behavior in `frontend/src/shared/api/` and reusable UI states in
  `frontend/src/shared/ui/`. **Components:** `frontend/src/api/`, pages,
  components, tests. **Requirements:** RS-1, RB-1. **TDD:** RED gateway/error
  tests, GREEN extraction, REFACTOR duplicate removal. **Verify:** frontend
  tests and build. **Done when:** components do not call `fetch` directly and
  revalidation/auth behavior is unchanged. **Depends:** F3.1. **Risk/rollback:**
  stale/error behavior; retain old gateways until parity passes.
- [ ] F3.3 — Feature modules
- **F3.3 — Feature modules:** **Objective:** move catalog, supplier, and
  inventory orchestration into feature folders. **Components:**
  `frontend/src/features/`, pages/hooks, route tests. **Requirements:** RS-1,
  RB-4. **TDD:** RED feature boundary/revalidation tests, GREEN move, REFACTOR
  shared primitives. **Verify:** `npm run test --prefix frontend`; build.
  **Done when:** routes, loading/error/empty states, mutations, and GET
  revalidation remain compatible. **Depends:** F3.2 and backend parity for the
  relevant capability. **Risk/rollback:** UI behavior drift; move one feature
  back to its prior module without API changes.
- [ ] F3.4 — Frontend quality tooling
- **F3.4 — Frontend quality tooling:** **Objective:** replace placeholder
  lint/format scripts only after dependency/workflow approval. **Components:**
  `frontend/package.json`, lockfile, CI job. **Requirements:** RB-3, RB-4.
  **TDD:** RED command-signaling checks, GREEN real scripts, REFACTOR CI/local
  invocation. **Verify:** `npm run test --prefix frontend`, `npm run lint --prefix
  frontend`, `npm run format --prefix frontend`, build. **Done when:** failures
  fail CI honestly and no type migration is implied. **Depends:** pending
  tooling decision. **Risk/rollback:** dependency or CI breakage; revert the
  tooling slice only.

### Phase 4 — Sales UI and controlled cutover

- [ ] S4.1 — Sales UI contract confirmation
- **S4.1 — Sales UI contract confirmation:** **Objective:** confirm specs
  012/014 and ledger parity before UI code. **Components:** sales specs,
  frontend gateways/routes, backend contract fixtures. **Requirements:** RB-1,
  RB-4. **TDD:** RED missing-contract checklist, GREEN approved fixture set,
  REFACTOR shared test helpers. **Verify:** backend/frontend contract tests.
  **Done when:** `/ventas` and `/ventas/historial` inputs, responses, errors,
  and auth are approved. **Depends:** B2.4 and F3.3. **Risk/rollback:** UI
  invents behavior; block implementation and keep route absent.
- [ ] S4.2 — Sales UI implementation
- **S4.2 — Sales UI implementation:** **Objective:** implement the two specified
  sales routes without new business capabilities. **Components:**
  `frontend/src/features/sales/`, shared API/UI, route tests. **Requirements:**
  RS-1, RB-1, RB-4. **TDD:** RED interaction/accessibility tests, GREEN UI,
  REFACTOR feature composition. **Verify:** `npm run test --prefix frontend`,
  build, approved browser/API smoke tests. **Done when:** authenticated flows,
  validation, loading/error states, and revalidation match confirmed specs.
  **Depends:** S4.1. **Risk/rollback:** sales consumer breakage; disable the
  routes and preserve backend contract.
- [ ] S4.3 — Controlled capability cutover
- **S4.3 — Controlled capability cutover:** **Objective:** enable one bounded
  capability at a time with shadow comparison and route-back. **Components:**
  deployment switch, observability, runbook, ledger. **Requirements:** RB-4,
  RS-5, RS-6. **TDD:** RED invalid-switch/stop-signal checks, GREEN staged
  cutover, REFACTOR runbook automation. **Verify:** authenticated smoke tests,
  metrics, rollback drill. **Done when:** success/stop thresholds, evidence,
  and last-known-good routing are demonstrated. **Depends:** T1.6, B2.x, S4.2.
  **Risk/rollback:** operational or data mismatch; halt and route back without
  database downgrade.

### Phase 5 — Tooling/CI, data migration, hardening, and retirement

- [ ] Q5.1 — Tooling/CI hardening
- **Q5.1 — Tooling/CI hardening:** **Objective:** align local/CI commands and
  independent diagnostics. **Components:** workflow, package scripts,
  `openspec/config.yaml` only if separately approved. **Requirements:** RB-3,
  RB-4. **TDD:** RED failure-propagation checks, GREEN aligned jobs, REFACTOR
  reporting. **Verify:** backend commands, frontend test/build/lint/format.
  **Done when:** command results are reproducible and no workspace claim is
  false. **Depends:** T0.5 and tooling decision. **Risk/rollback:** CI blind
  spot; revert workflow only.
- [ ] D5.1 — Additive data rehearsal
- **D5.1 — Additive data rehearsal:** **Objective:** rehearse an approved
  forward-only migration with backups, IDs/timestamps, counts/checksums, and
  mismatch handling. **Components:** new Alembic revision, rehearsal scripts,
  reconciliation record. **Requirements:** RB-2, RS-6. **TDD:** RED mismatch
  and idempotency checks, GREEN rehearsal, REFACTOR reporting. **Verify:**
  `alembic upgrade head`, approved PostgreSQL checks. **Done when:** evidence
  is preserved and no historical record is edited/deleted. **Depends:** approved
  data-migration decision and B2.3. **Risk/rollback:** lossy migration; stop before
  production writes and discard only rehearsal database.
- [ ] C5.1 — Hardening and rollback drill
- **C5.1 — Hardening and rollback drill:** **Objective:** run approved
  PostgreSQL/concurrency/performance evidence and a cutover rollback drill.
  **Components:** deployment switch, metrics, runbook, incident/reconciliation
  record. **Requirements:** RS-5, RS-6, RB-4. **TDD:** RED stop-signal checks,
  GREEN drill, REFACTOR operational evidence. **Verify:** approved DB tests,
  smoke suite, rollback verification. **Done when:** route-back, evidence
  retention, and reconciliation are demonstrated. **Depends:** S4.3, D5.1.
  **Risk/rollback:** unresolved mismatch; stop cutover and preserve evidence.
- [ ] R5.1 — Retirement
- **R5.1 — Retirement:** **Objective:** remove superseded internals only after
  parity, monitoring, rollback, and historical evidence are durable.
  **Components:** old backend/frontend modules, CI/deployment references,
  ledger. **Requirements:** RB-4, RS-1, RS-6. **TDD:** RED dependency/search
  checks, GREEN removal, REFACTOR documentation. **Verify:** full backend and
  frontend suites, build, migration/history checks. **Done when:** no route or
  rollback target depends on retired code and the ledger is updated. **Depends:**
  C5.1 and explicit retirement approval. **Risk/rollback:** premature removal;
  retain a deployable tagged previous version and restore only application code.

## Review Workload Forecast

| Track | Planned review units | Expected change size | Gate |
|---|---:|---:|---|
| Phase 0 ledger/evidence | 6 | 100–300 lines/artifacts each | Baseline revision approved |
| Phase 1 backend seams | 5 | 100–350 lines each | Contract, auth, transaction parity |
| Phase 1 observability/gate | 2 | 100–300 lines each | Stop/rollback evidence |
| Backend modularization | 4+ | <=400 changed lines each | Capability-level parity |
| Frontend foundation | 4 | <=400 changed lines each | Route/API/UI regression |
| Sales UI | 3 | <=400 changed lines each | Specs 012/014 and smoke tests |
| Tooling/CI | 1–2 | <=400 changed lines each | Command evidence and failure propagation |
| Data migration | 1 per migration/rehearsal | <=400 changed lines each | Counts/checksums/reconciliation |
| Cutover/retirement | 2+ | <=400 changed lines each | Rollback drill and ledger update |

No task should combine backend, frontend, tooling, data, and cutover changes
in one review unit. If an implementation exceeds 400 changed lines, split it
by capability or seam before review; do not remove required evidence to meet
the budget.

## Pending decisions

1. Is PostgreSQL mandatory for migration rehearsal and concurrency verification,
   and which slices may use SQLite beyond fast unit tests?
2. Does compatibility include undocumented client behavior, or only documented
   `/api/v1` contracts and current consumers?
3. Will the backend remain FastAPI/SQLAlchemy, or must a future framework/ORM
   decision precede adapter-interface implementation?
4. Will the frontend remain JavaScript ES2022, or is TypeScript a separately
   approved migration?
5. Which deployment mechanism supplies the allowlisted capability switch and
   last-known-good routing control?
6. What approved workspace command, if any, can eventually support changing
   `strict_tdd` and cross-project verification?
7. Which observability sink and retention policy preserve cutover metrics,
   audit evidence, and rollback reconciliation?
