# Executable Quality Baseline

Baseline revision: `BL-20261021-01`; source revision `5ca3881`; observed
2026-10-21 UTC on Windows with Python 3.14.3 and Node/Vite dependencies already
installed. Commands were run independently from their project roots.

| Project / command | Result | Context and evidence | Warnings/failures |
|---|---|---|---|
| Backend `PYTHONPATH=. pytest -v` | PASS — 473 passed | repository root; SQLite development DB; JWT env set | 10 dependency warnings, including PyJWT key-length warnings |
| Backend `pytest --cov=app --cov-report=term-missing` | PASS — 473 passed; 90% total | repository root; coverage report in command output | 240 warnings, mainly ResourceWarning/dependency warnings |
| Backend `ruff check .` | PASS — all checks passed | repository root; same local environment | none |
| Backend `ruff format --check .` | PASS — 123 files formatted | repository root | none |
| Backend `mypy app` | PASS — no issues in 34 source files | repository root | none |
| Backend `alembic upgrade head` + `alembic current` | PASS — head `2c3245f4f658` | current SQLite development database | PostgreSQL rehearsal not performed |
| Frontend `npm run test --prefix frontend` | PASS — 40 files, 322 tests | frontend project; Node test runner + Vitest | React `act(...)` and deprecated `ReactDOMTestUtils.act` warnings |
| Frontend `npm run build --prefix frontend` | PASS — Vite build, 64 modules | frontend project; `VITE_API_URL=http://localhost:8000` for build | none |
| Frontend `npm run lint --prefix frontend` | NOT A QUALITY GATE — echo placeholder | `frontend/package.json` script | reports `lint: no configurado aún — T20`; no lint executed |
| Frontend `npm run format --prefix frontend` | NOT A QUALITY GATE — echo placeholder | `frontend/package.json` script | reports `format: no configurado aún — T20`; no format executed |
| Root `pytest -q` | PASS — 473 passed | root invocation also succeeds in current environment | previous implementation/design recorded import-drift concern; no cross-project command exists |

## Local/CI invocation drift

- CI backend runs `ruff check . --select E4,E7,E9,F`, `ruff format --check .`,
  `mypy app --ignore-missing-imports`, Alembic, and
  `PYTHONPATH=. pytest -v --cov=app --cov-report=term-missing`.
- Local evidence above runs the configured commands. CI uses an explicit
  `PYTHONPATH` and ignores missing mypy imports; this is a command-context
  difference and remains visible.
- CI frontend runs `npm run test` and `npm run build` from `frontend`; it does
  not run the placeholder lint/format scripts.
- `openspec/config.yaml` has `strict_tdd: false` and an empty
  `workspace_test_command` (no approved workspace command). No cross-project
  pass is claimed. Standard-mode
  implementation tasks still require practical RED-GREEN-REFACTOR evidence.
