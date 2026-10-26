# Baseline Release Gate

This checklist is the Release gate for every later replacement slice. T0.1
defines the gate; the baseline is not approved until the evidence is populated
and reviewed.

## Gate identity

- Baseline revision: `BL-20261021-01`
- Reviewed by: `SDD apply evidence review`
- Review date (UTC): `2026-10-21`
- Last-known-good rollback target: `28f8318` — last validated application
  commit with green backend/frontend CI; rollback route is redeploying this
  commit and stopping the incompatible slice.
- Gate status: `BLOCKED` — baseline evidence is populated, but release approval
  requires the named blockers below.

## Required evidence

- [x] 100% of documented `/api/v1` endpoints have method, path, authentication,
      request/response schemas, normalization, status/error semantics,
      ordering, consumer ownership, classification, and source evidence.
- [x] Frontend consumers are linked to the endpoint entries without treating
      undocumented assumptions as desired contracts.
- [x] Compatibility-critical tables, columns, foreign keys, identifiers,
      timestamps, and applied migration revisions are recorded.
- [x] `movimientos_inventario`, `ventas`, and `venta_items` are explicitly
      protected as append-only historical evidence.
- [x] Stock derivation and sale-to-movement atomicity/traceability have
      representative executable evidence or an explicit blocker.
- [x] Backend and frontend test, coverage, lint, format, typecheck, and build
      commands are recorded with project root, result, revision, timestamp,
      warnings, and failures.
- [x] Local/CI invocation drift and the absence of a workspace command are
      visible; no cross-project pass is claimed without a workspace command.
- [x] Every mismatch is classified as a deviation or reconciliation blocker,
      with both sources preserved and no repair write performed.
- [x] Every assumption, dependency, and open decision has an owner or named
      next action.

## Later-slice admission checks

Before implementation or cutover of a bounded slice, confirm:

- [ ] The slice references this approved baseline revision and exact affected
      ledger entries.
- [ ] Preserved API, authentication, normalization, response, status/error,
      ordering, and data invariants are characterized for the slice.
- [ ] New evidence and unresolved deviations are recorded before cutover.
- [ ] A deployable last-known-good implementation and application/deployment
      rollback route are named.
- [ ] Stop signals cover contract, authentication, transaction, stock/history,
      reconciliation, and relevant quality failures.
- [ ] Rollback stops incompatible writes and preserves accepted writes, logs,
      and audit evidence for append-only reconciliation.
- [ ] No destructive migration, historical edit/delete, migration downgrade,
      implicit contract change, or unapproved business capability is included.

## Decision

- [ ] `APPROVED` — all applicable evidence is present and blockers are resolved.
- [ ] `BLOCKED` — missing evidence/open decisions are listed below.

Blocking items:

1. **Deployment owner:** ✅ resolved — `28f8318` is the named last-known-good
   application commit; redeploying it is the application-level route-back.
2. **Data/deployment owner:** provide production table counts/checksums and
   approve PostgreSQL migration/concurrency rehearsal scope before persistence
   cutover.
3. **Maintainer:** resolve compatibility scope for undocumented clients and
   identify the observability sink/retention policy for cutover evidence.
