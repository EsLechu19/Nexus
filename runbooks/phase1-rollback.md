# Phase 1 rollback runbook

## Scope

The known-good application remains the rollback target while safety seams are
characterized. A capability switch must be allowlisted and defaults to the
known-good path when missing or invalid.

## Stop signals

Stop the cut when contract status/error or authentication parity fails, a
transaction fails, stock becomes negative, historical counts/checksums differ,
or local operational errors exceed the approved threshold.

## Procedure

1. Disable the replacement capability switch and route traffic to the
   deployable `last-known-good` version.
2. Stop writes to any incompatible replacement target.
3. Preserve structured logs, accepted writes, and correlation identifiers.
4. Reconcile accepted writes using append-only correction evidence.
5. Re-run contract, authentication, transaction, stock, and history checks.
6. Record the incident and reconciliation result before retrying the cut.

Rollback is an application/deployment action. It must not downgrade the
database, edit or delete historical inventory movements or sales, or rewrite
applied migrations. Production sink ownership and retention remain an open
operational decision; development logs are local and secret-free.
