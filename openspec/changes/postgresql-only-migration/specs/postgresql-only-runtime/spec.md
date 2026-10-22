# PostgreSQL-Only Runtime Specification

## Purpose

Define the PostgreSQL 18 boundary for the Nexus application, Alembic, and CI without exposing credentials or permitting accidental SQLite execution.

## Requirements

### Requirement: PostgreSQL-only application runtime

The application runtime MUST require a valid PostgreSQL connection URL in every environment. It MUST reject SQLite URLs, missing URLs, and unsupported database schemes before creating an application database engine. Runtime diagnostics MUST NOT include passwords, tokens, or complete credential-bearing URLs.

#### Scenario: Application starts with PostgreSQL

- GIVEN a valid PostgreSQL URL is supplied through the approved environment mechanism
- WHEN the application initializes its database dependencies
- THEN the application creates a PostgreSQL-backed engine and completes startup without selecting SQLite

#### Scenario: Application rejects SQLite

- GIVEN `DATABASE_URL` uses a SQLite scheme
- WHEN the application initializes its database dependencies
- THEN startup fails deterministically with a safe configuration error
- AND no SQLite engine or `nexus.db` file is created

#### Scenario: Application rejects missing or unsupported configuration

- GIVEN the database URL is missing or uses an unsupported scheme
- WHEN the application initializes its database dependencies
- THEN startup fails before opening a database connection
- AND the failure output does not disclose credentials

### Requirement: PostgreSQL-only Alembic execution

Alembic online and offline execution MUST consume the approved environment-provided PostgreSQL URL rather than a committed SQLite URL. Alembic MUST reject SQLite and unsupported schemes before applying or rendering migrations. Existing applied revisions MUST NOT be rewritten; any required schema correction MUST be forward-only.

#### Scenario: Clean PostgreSQL migration chain

- GIVEN a disposable PostgreSQL 18 database and the approved PostgreSQL URL
- WHEN Alembic applies the complete migration chain
- THEN every revision succeeds in order
- AND the resulting schema includes all six application tables, including empty `ventas` and `venta_items`

#### Scenario: Alembic rejects SQLite in online mode

- GIVEN Alembic receives a SQLite URL
- WHEN an online migration is requested
- THEN Alembic fails before applying a revision
- AND it does not create or modify `nexus.db`

#### Scenario: Applied history remains immutable

- GIVEN the existing Alembic chain contains applied revisions
- WHEN PostgreSQL compatibility requires a schema correction
- THEN the correction is represented as a new forward migration
- AND no applied migration file or revision identity is rewritten

### Requirement: PostgreSQL-backed CI gate

CI MUST provision PostgreSQL 18 for database-dependent tests and migration checks. CI MUST apply Alembic against that PostgreSQL service and MUST NOT provision, select, or use SQLite as a runtime or migration database. CI MUST fail when the application or migration configuration permits a SQLite URL.

#### Scenario: CI validates the PostgreSQL path

- GIVEN the CI workflow starts with its PostgreSQL 18 service available
- WHEN it runs migration and database-dependent tests
- THEN the tests use the PostgreSQL service
- AND Alembic reaches the expected head revision

#### Scenario: CI catches a SQLite regression

- GIVEN a CI configuration or runtime default reintroduces a SQLite database URL
- WHEN the CI PostgreSQL-only checks run
- THEN the workflow fails with an actionable configuration error
- AND the workflow does not report a database-backed pass based on SQLite

### Requirement: Safe credential delivery and operational documentation

Database credentials MUST be delivered through approved environment or CI secret mechanisms and MUST NOT be committed in source, fixtures, migration artifacts, manifests, or logs. Documentation MUST describe URL injection, redaction expectations, local PostgreSQL rehearsal, and the prohibition on production access during implementation.

#### Scenario: Credential-bearing configuration is used safely

- GIVEN a credential-bearing PostgreSQL URL is injected through an approved secret mechanism
- WHEN runtime, Alembic, or CI diagnostics are emitted
- THEN diagnostics redact credentials and do not persist the complete URL

#### Scenario: Repository remains credential-free

- GIVEN source, CI configuration, documentation, and migration evidence are inspected
- WHEN a credential scan is run
- THEN no password, token, or production connection secret is present

## Pending Decisions

- The PostgreSQL database name, role, and schema MUST be approved before implementation or cutover.
- The credential delivery mechanism MUST be approved before implementation or cutover.
- The permitted PostgreSQL 18 local rehearsal target MUST be confirmed before execution.
- SQLite MAY remain available only for isolated unit tests, but this policy is unresolved and MUST be decided before test migration work is finalized.
