# Migration Validation and Cutover Specification

## Purpose

Define machine-readable parity evidence, acceptance gates, sequence safety, rollback, archive handling, and operational documentation for PostgreSQL migration rehearsal and cutover.

## Requirements

### Requirement: Machine-readable migration manifest

Every rehearsal and cutover attempt MUST emit a machine-readable manifest containing source and target identities, schema revisions, export metadata, per-table counts, canonical checksums, foreign-key results, timestamp and decimal policies, sequence values, and validation outcomes. The manifest MUST identify failures and MUST NOT contain credentials.

#### Scenario: Validated rehearsal emits complete evidence

- GIVEN a deterministic export has been imported into disposable PostgreSQL 18
- WHEN validation runs
- THEN the manifest contains all required source, target, count, checksum, FK, policy, sequence, and outcome fields
- AND the manifest can be inspected without database credentials

#### Scenario: Validation fails

- GIVEN any required parity or integrity check fails
- WHEN the manifest is finalized
- THEN the manifest records the failed check and relevant table or row scope
- AND the migration is not marked accepted

### Requirement: Parity and integrity acceptance gates

Acceptance MUST require matching per-table counts and approved canonical checksums, zero orphaned foreign keys, preserved IDs and timestamps, approved decimal semantics, and no duplicate or incomplete rows. Any mismatch, ambiguity, or missing evidence MUST block acceptance.

#### Scenario: Source and target achieve parity

- GIVEN all six application tables have been imported
- WHEN counts, canonical checksums, foreign keys, IDs, timestamps, nullable values, and decimal values are compared
- THEN every required check passes with zero orphaned references
- AND the migration is eligible for the remaining cutover gates

#### Scenario: A parity check detects divergence

- GIVEN a target count, checksum, timestamp, decimal, ID, or FK result differs from the approved source result
- WHEN acceptance validation runs
- THEN acceptance is blocked
- AND the evidence identifies the divergence for remediation or rollback

### Requirement: PostgreSQL sequence safety

After import, every identity sequence for a populated application table MUST be advanced above the imported maximum ID. For empty tables, sequence state MUST remain valid for the next generated ID. Validation MUST prove that the next generated ID cannot collide with an imported ID.

#### Scenario: Populated table receives a new row

- GIVEN a table has imported IDs and its sequence has been repaired
- WHEN the next normal application insert occurs
- THEN the generated ID is greater than the imported maximum
- AND no primary-key collision occurs

#### Scenario: Sequence repair evidence is incomplete

- GIVEN any populated table lacks a recorded post-import sequence value or next-ID check
- WHEN acceptance validation runs
- THEN acceptance is blocked
- AND the target is not treated as ready for cutover

### Requirement: Append-only and concurrency validation

Validation MUST verify that migration and rollback procedures do not update or delete historical inventory movements or sales. PostgreSQL-backed tests MUST cover the relevant concurrency behavior that SQLite cannot establish, including sale stock deduction where applicable, without changing stock or sale semantics.

#### Scenario: Historical immutability holds

- GIVEN movement and sale rows exist in the source snapshot
- WHEN migration, validation, and rollback rehearsal complete
- THEN no historical movement or sale row has been updated or deleted
- AND any newly accepted target records remain append-only evidence

#### Scenario: PostgreSQL concurrency behavior is exercised

- GIVEN concurrent sale operations are run against disposable PostgreSQL 18
- WHEN the concurrency test completes
- THEN row-lock and stock-deduction behavior is validated against the approved existing semantics
- AND SQLite-only results are not accepted as proof of concurrency safety

### Requirement: Non-destructive rollback and cutover gates

Before acceptance, an operational rollback MUST stop target writes, preserve the target database and all manifests/logs, and route the application back only to the unchanged authoritative SQLite snapshot under the approved procedure. Rollback MUST NOT delete target data or downgrade Alembic. Any writes accepted on PostgreSQL MUST be captured for append-only reconciliation before another attempt. After acceptance, PostgreSQL MUST be the sole application database.

#### Scenario: Cutover acceptance succeeds

- GIVEN rehearsal, parity, sequence, append-only, credential, and documentation gates all pass
- WHEN the authorized cutover is approved
- THEN application writes are directed to PostgreSQL
- AND PostgreSQL is recorded as the sole application database
- AND the SQLite snapshot is retained as read-only archive evidence

#### Scenario: Cutover acceptance fails

- GIVEN any acceptance gate fails before PostgreSQL becomes authoritative
- WHEN rollback is invoked
- THEN target writes stop
- AND the application routes back to the unchanged SQLite snapshot only through the approved procedure
- AND target data and evidence remain preserved for diagnosis and append-only reconciliation

### Requirement: Read-only archive and operational runbook

The project MUST document dry run, write freeze, cutover, validation, rollback, credential injection, archive access, and retention handling. `nexus.db`, manifests, checksums, and logs MUST be retained read-only as audit and rollback evidence until the approved archive policy permits a change. No production or remote execution is part of implementation or rehearsal.

#### Scenario: Runbook dry run is completed

- GIVEN an authorized local or disposable rehearsal environment
- WHEN the documented migration runbook is executed in dry-run mode
- THEN each prerequisite, freeze, validation, rollback, and archive step produces an observable result
- AND no production connection or credential discovery is attempted

#### Scenario: Archive evidence is accessed

- GIVEN migration acceptance is complete or rollback diagnosis is required
- WHEN an operator accesses the preserved source or evidence
- THEN the artifacts are read-only and access follows the approved controls
- AND retention status is recorded without deleting historical evidence prematurely

## Pending Decisions

- The checksum algorithm, version, and canonical serialization MUST be approved before a manifest can be accepted.
- The archive retention period and access controls MUST be approved before final cutover.
- The rollback reconciliation procedure for writes accepted on PostgreSQL MUST be approved before cutover.
- The exact write-freeze and tolerated-downtime policy MUST be approved before operational execution.
