# Apply Progress: backend-frontend-replacement

## Mode

- Standard mode (`strict_tdd: false`; no approved workspace-wide test command).
- Assigned scope: Phase 1, T1.1–T1.7. Phase 0 T0.1–T0.6 is retained.
- Delivery strategy: ask-on-risk; review budget: 400 changed lines.
- Baseline revision: `BL-20261021-01`; rollback reference: `origin/master` was
  not verified as deployable in this local apply and is not claimed as a
  confirmed last-known-good runtime target.

## Completed tasks

- [x] T0.1 — Freeze baseline scope and evidence template
- [x] T0.2 — Inventory documented API and frontend consumers
- [x] T0.3 — Capture representative contract fixtures
- [x] T0.4 — Inventory schema, migrations, and historical invariants
- [x] T0.5 — Establish executable backend/frontend quality baseline
- [x] T0.6 — Approve Phase 0 release gate (evaluated; gate remains BLOCKED)
- [x] T1.1 — Add validated configuration/provider seam
- [x] T1.2 — Characterize authentication-before-database behavior
- [x] T1.3 — Define explicit request dependency and unit-of-work boundary
- [ ] T1.4 — Characterize sale atomicity and canonical movement operation
- [x] T1.5 — Add compatibility presenters and contract regression gates
- [x] T1.6 — Add observability, stop signals, and rollback runbook
- [ ] T1.7 — Approve Phase 1 safety-seam gate

## Work unit evidence

| Evidence | Result |
|---|---|
| Focused test command and exact result | `PYTHONPATH=. pytest -q tests/test_phase1_safety_seams.py tests/test_venta_atomicidad_T05_012.py tests/test_ventas_post_T06_012.py tests/test_integracion_movimientos_T13.py tests/test_auth_login_T06_011.py tests/test_proteccion_T08_011.py` — 31 passed, 5 warnings. |
| Full backend test command and exact result | `PYTHONPATH=. pytest -v` initially reached 477 passed with 4 format-check failures; after formatting authored files, final `PYTHONPATH=. pytest -q` passed 481 tests with 10 warnings. |
| Backend quality commands | `ruff check .` passed; `ruff format --check .` passed after formatting authored files; `mypy app` passed for 39 files. |
| Frontend quality commands | `npm run test --prefix frontend` — 40 files / 322 tests passed; `npm run build --prefix frontend` passed with 64 modules. Existing React `act(...)` warnings remain separately reported. |
| Migration evidence | `alembic upgrade head; alembic current` passed; current head is `2c3245f4f658`. No migration was created or edited. |
| Runtime harness command/scenario and exact result | Backend `TestClient` auth protection and sale flows passed in the focused suite; frontend Vitest/build passed. No authorized PostgreSQL runtime was available, so PostgreSQL concurrency rehearsal is unavailable and not claimed. |
| Rollback boundary | Revert only Phase 1 seam modules/tests/runbook/ledger and the five newly marked Phase 1 checkboxes plus this progress record. Keep Phase 0 evidence and all historical data/migrations. Runtime rollback defaults to the known-good implementation; no database downgrade is authorized. |

## Implementation evidence

- `app/config.py` validates environment-driven `DATABASE_URL` and JWT
  configuration; `app/services/auth_service.py` consumes that provider for
  JWT secrets, production rejects SQLite, and errors omit values.
- `app/database.py` composes the validated database URL while preserving
  SQLite test compatibility.
- `app/services/unit_of_work.py` owns one session lifecycle and one commit or
  rollback decision.
- `app/services/movimiento_service.py` exposes `preparar_salida` so sales use
  the canonical movement construction without an independent commit.
- `app/services/venta_service.py` now uses the unit of work and canonical
  movement operation; existing atomicity/traceability tests pass.
- `app/compatibility.py`, `app/cutover.py`, and `app/observability.py` add
  presenter, allowlisted route fallback, and secret-free structured signals.
- `runbooks/phase1-rollback.md` documents stop signals and application-level
  rollback without historical edits.
- `ledger/phase1-safety-seams.md` records the evidence and limitations.

## Blockers and deviations

- T1.4 remains unchecked: PostgreSQL concurrency verification was unavailable
  in the authorized local environment. SQLite characterization passed, but it
  is not a substitute for the required concurrency evidence.
- T1.7 remains unchecked: Phase 1 cannot be approved while T1.4 is pending and
  `origin/master` has not been verified as deployable last-known-good.
- No production data, production sink, credentials, remote service, or
  production database was accessed.
- No business capability, API contract, schema, applied migration,
  `strict_tdd`, or `openspec/config.yaml` was changed.

## Remaining tasks

- [ ] T1.4 — PostgreSQL concurrency rehearsal and final sale discrepancy gate
- [ ] T1.7 — Phase 1 safety-seam gate after T1.4 and rollback-target evidence

## Next gate

Phase 2+ remains blocked until T1.4 is completed with authorized PostgreSQL
evidence and T1.7 records a reviewed gate with a verified deployable rollback
target.
