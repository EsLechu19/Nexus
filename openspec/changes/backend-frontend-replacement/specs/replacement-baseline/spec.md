# Replacement Baseline Specification

## Purpose

This capability establishes an evidence-based baseline and maintained contract ledger before any backend or frontend replacement slice is implemented. It records current facts, documented contracts, observed deviations, and unresolved decisions without silently changing existing product behavior.

## Requirements

### Requirement: Complete contract ledger

The program MUST maintain a versioned contract ledger covering 100% of the documented `/api/v1` endpoints across the existing catalog, supplier, inventory movement, stock, authentication, and sales capabilities, plus the frontend consumers that depend on them.

The ledger MUST record, for each endpoint, method and path, authentication requirement, request and response schemas, normalization rules, status codes, error vocabulary, relevant ordering semantics, consumer ownership, and source evidence. It MUST distinguish documented contract, observed behavior, deviation, assumption, dependency, and open decision.

The ledger MUST NOT promote an accidental observed behavior to a desired contract without an approved requirement or decision record.

#### Scenario: Ledger covers the documented API surface

- GIVEN the existing backend and specifications define documented `/api/v1` endpoints
- WHEN the baseline is reviewed for release-gate approval
- THEN every documented endpoint has a ledger entry with its method, path, authentication, request and response contract, status/error semantics, normalization, consumer, and evidence source
- AND every entry is classified as a contract, observed behavior, deviation, assumption, dependency, or open decision

#### Scenario: Observed behavior differs from the documented contract

- GIVEN an endpoint's implementation or runtime evidence differs from its existing specification
- WHEN the discrepancy is recorded in the ledger
- THEN the discrepancy is marked as a deviation with both sources preserved
- AND the deviation is not treated as permission to change the endpoint behavior during the baseline or safety-seam phases

### Requirement: Persistence and historical-invariant baseline

The ledger MUST inventory the compatibility-critical tables, columns, foreign keys, migration versions, historical identifiers and timestamps, and protections relevant to `movimientos_inventario`, `ventas`, `venta_items`, products, suppliers, and users.

The baseline MUST explicitly record that inventory movements and sales are append-only evidence, that applied migrations are not edited, and that stock and sale-to-movement traceability invariants are preserved. It MUST include representative fixtures or equivalent executable evidence for the stock formula and sale atomicity/traceability.

#### Scenario: Historical inventory and sales are baselined

- GIVEN the repository contains inventory movements and sales history
- WHEN the persistence baseline is approved
- THEN the ledger identifies the tables, relationships, immutable fields, migration history, and append-only protections for that history
- AND representative evidence verifies stock derivation and successful sale-to-movement links

#### Scenario: A historical mismatch is detected

- GIVEN a baseline check finds a count, identifier, timestamp, quantity, price, total, movement type, or relationship mismatch
- WHEN the mismatch is recorded
- THEN it is classified as a deviation or reconciliation blocker with preserved evidence
- AND the baseline MUST NOT silently rewrite or delete historical records to make the check pass

### Requirement: Reproducible quality baseline

The program MUST record executable backend and frontend test, coverage, lint, format, typecheck, and build commands together with their local or CI context, result, timestamp or revision, warnings, and failures.

The baseline MUST report warnings separately from pass/fail evidence and MUST identify invocation drift between local and CI commands. It MUST NOT claim cross-project verification when no workspace command executes both projects.

#### Scenario: Backend and frontend commands are independently evidenced

- GIVEN the backend and frontend are configured as independent projects
- WHEN baseline quality evidence is collected
- THEN the evidence records the configured commands and their actual results for each project separately
- AND frontend warnings or backend invocation failures are visible without being mislabeled as passing checks

#### Scenario: No workspace test command exists

- GIVEN `openspec/config.yaml` has no workspace test command and `strict_tdd` is `false`
- WHEN the baseline records the SDD/TDD tooling state
- THEN it records that independent project-level RED-GREEN-REFACTOR evidence remains required for implementation tasks
- AND it records the absence of a workspace command as a tooling limitation and decision boundary
- AND it MUST NOT change `strict_tdd` or the OpenSpec configuration in this capability

### Requirement: Baseline release gate and change traceability

Every later replacement slice MUST reference the approved baseline revision, update affected ledger entries before cutover, and identify its bounded capability, preserved contracts, new evidence, unresolved deviations, and rollback target.

No replacement slice MAY be considered ready for implementation or cutover if the affected ledger coverage, contract characterization, data invariants, quality evidence, or open decisions required by its scope are missing.

#### Scenario: A bounded replacement slice is proposed

- GIVEN a later change intends to replace one bounded backend or frontend capability
- WHEN the change is prepared for implementation or cutover
- THEN it references a baseline revision and identifies the exact ledger entries it affects
- AND it includes evidence that preserved contracts and relevant data invariants are characterized
- AND it names a deployable last-known-good rollback target

#### Scenario: Required baseline evidence is missing

- GIVEN a proposed slice lacks coverage for an affected endpoint, invariant, quality command, or rollback target
- WHEN the release gate is evaluated
- THEN the slice is blocked from cutover
- AND the missing evidence is recorded as an explicit open item rather than inferred or waived silently

## Explicit boundaries

- This capability MUST NOT introduce new business requirements or alter existing API, authentication, stock, sales, normalization, status, error, or append-only semantics.
- This capability MUST NOT authorize a flag-day rewrite, destructive migration, migration downgrade that removes historical facts, or source-code implementation.
- Future behavior changes require a separate approved delta specification.
