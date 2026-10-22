# Offline Data Migration Specification

## Purpose

Define a deterministic, repeatable, write-frozen migration of the six application tables from the preserved `nexus.db` snapshot to PostgreSQL while retaining application identity and historical meaning.

## Requirements

### Requirement: Immutable source snapshot identification

The migration process MUST treat `nexus.db` as a read-only source. Before export it MUST record enough identity to distinguish the exact source snapshot, including path, size, content hash, schema revision, and export timestamp. It MUST NOT modify, delete, or replace the source file.

#### Scenario: Source snapshot is identified before export

- GIVEN the approved `nexus.db` file exists and is readable
- WHEN a migration dry run begins
- THEN the process records the source identity and schema revision in migration evidence
- AND the source file remains byte-for-byte unchanged

#### Scenario: Source snapshot is missing or changes during preparation

- GIVEN the source file is missing or its identity changes after identification
- WHEN export or import is requested
- THEN the migration stops before loading rows
- AND the failure identifies the source-integrity gate without exposing secrets

### Requirement: Explicit write freeze and deterministic export

The migration MUST require an approved write freeze before the authoritative export. The export MUST be deterministic in table and row ordering and MUST include all rows in `usuarios`, `productos`, `proveedores`, `movimientos_inventario`, `ventas`, and `venta_items`, including zero-row tables. The process MUST NOT use dual-write or live replication.

#### Scenario: Export runs under an approved freeze

- GIVEN the source identity is recorded and the approved write freeze is active
- WHEN the authoritative export runs
- THEN the six application tables are exported in a deterministic order
- AND the export records zero counts explicitly for empty tables
- AND no source write is accepted during the export window

#### Scenario: Export is attempted without a freeze

- GIVEN no approved write-freeze signal exists
- WHEN an authoritative export is requested
- THEN the process refuses to continue
- AND it does not produce an importable cutover snapshot

### Requirement: Parent-first import with identity preservation

The importer MUST load parent data before dependent data in this order: `usuarios`, `productos`, `proveedores`, `movimientos_inventario`, `ventas`, and `venta_items`. It MUST preserve source integer IDs, timestamps, nullable values, foreign keys, and monetary `Decimal` values. It MUST preserve password hashes as opaque values and MUST NOT recreate users from plaintext credentials.

#### Scenario: Complete snapshot imports successfully

- GIVEN a write-frozen export passes source-integrity checks and a PostgreSQL schema exists at the approved Alembic revision
- WHEN the import runs
- THEN all six tables receive the corresponding source rows in the specified order
- AND every imported ID, timestamp, nullable value, foreign key, and monetary value is preserved according to the approved policies
- AND password hashes are copied without plaintext reconstruction

#### Scenario: Foreign-key dependency or duplicate identity fails

- GIVEN an export contains an orphaned reference or an ID that conflicts with a target row
- WHEN the importer validates or loads that row
- THEN the import stops without accepting a partially valid cutover
- AND the evidence identifies the table and constraint failure

#### Scenario: Empty sales tables are represented

- GIVEN the source contains zero rows in `ventas` and `venta_items`
- WHEN the import completes
- THEN both PostgreSQL tables exist
- AND their validated imported counts are explicitly zero

### Requirement: Historical and security data remain immutable

The migration MUST NOT update or delete source movement or sale records. It MUST preserve historical IDs and values as append-only evidence. It MUST NOT copy pytest fixtures, generated users, CI data, compiled files, or unrelated sample data into the application target.

#### Scenario: Historical rows are imported without mutation

- GIVEN the source contains inventory movements or sales history
- WHEN the target import and parity validation complete
- THEN each historical row is present with its preserved identity and values
- AND no source or target historical row was updated or deleted by the migration

#### Scenario: Non-source test data is encountered

- GIVEN test fixtures or generated CI records exist outside the six-table source snapshot
- WHEN the migration scope is evaluated
- THEN those records are excluded from the application-data import
- AND they are recreated only by isolated test fixtures when needed

### Requirement: Migration test fixtures are isolated from production-data migration

Migration tests MUST use a disposable PostgreSQL 18 target and fixtures that can distinguish source application rows from generated test rows. SQLite MAY be used for isolated unit tests only if the pending test-policy decision explicitly permits it; SQLite MUST NOT be used to validate runtime, Alembic, CI database provisioning, or migration parity.

#### Scenario: Rehearsal uses disposable PostgreSQL

- GIVEN a migration fixture set and a disposable PostgreSQL 18 target
- WHEN the migration rehearsal runs
- THEN it verifies import, foreign keys, decimals, timestamps, IDs, sequences, and append-only behavior against PostgreSQL
- AND it does not depend on production or remote credentials

#### Scenario: Test-only SQLite policy is not approved

- GIVEN the project has not approved SQLite for isolated unit tests
- WHEN database fixtures are selected
- THEN database-dependent fixtures use PostgreSQL
- AND no SQLite fixture is treated as evidence of PostgreSQL migration correctness

## Pending Decisions

- The interpretation and normalization of existing naive SQLite timestamps MUST be approved and tested before import.
- The export format and canonical serialization MUST be approved before implementation.
- The checksum algorithm and version MUST be approved before import evidence is accepted.
- The exact write-freeze owner, procedure, and tolerated downtime MUST be approved before cutover.
- Whether SQLite remains allowed for isolated unit tests MUST be decided before fixtures are finalized.
- Any non-application SQLite tables excluded from migration MUST be explicitly identified after the complete schema audit.
