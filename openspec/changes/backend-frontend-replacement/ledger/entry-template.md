# Ledger Entry: <entry identifier and title>

Copy this template for one ledger entry. Replace every placeholder and retain
`N/A — reason` when a field does not apply. Do not infer desired behavior from
an observation.

## Classification and identity

| Field | Value |
|---|---|
| Entry ID | `<capability>-<kind>-<sequence>` |
| Classification | `documented contract` / `observed behavior` / `deviation` / `assumption` / `dependency` / `open decision` |
| Baseline revision | `BL-YYYYMMDD-NN` |
| Source revision | `<Git commit, tag, or working-tree marker>` |
| Owner/reviewer | `<name or role>` |
| Last reviewed | `<UTC date>` |

## Endpoint and consumer contract

| Field | Value |
|---|---|
| Endpoint | `<HTTP method> <path>` or `N/A — reason` |
| Authentication requirement | `<public, Bearer, or other current requirement>` |
| Request schema | `<schema/module and representative shape>` |
| Response schema | `<schema/module and representative shape>` |
| Normalization | `<trim/case/default/order behavior>` |
| Status/error semantics | `<success, validation, auth, not-found/conflict statuses and bodies>` |
| Ordering semantics | `<explicit ordering or N/A — reason>` |
| Consumer ownership | `<frontend module, external owner, or N/A — reason>` |

## Data and invariant baseline

| Field | Value |
|---|---|
| Data | `<tables, columns, foreign keys, IDs, timestamps, or N/A — reason>` |
| Historical/append-only invariant | `<protected fields and insert-only expectation>` |
| Stock invariant | `<initial stock + entries - exits, or N/A — reason>` |
| Sale traceability/atomicity | `<sale-item-movement relationship and failure behavior>` |
| Migration evidence | `<current head, applied revisions, or N/A — reason>` |

## Quality and evidence

| Field | Value |
|---|---|
| Quality | `<backend/frontend command and project root>` |
| Result | `<pass, fail, warning, or unavailable>` |
| Runtime context | `<local/CI, dependencies, database, and configuration class>` |
| Evidence | `<fixture, test name, output path, log, OpenAPI snapshot, or source link>` |
| Observed at | `<UTC timestamp and source revision>` |
| Warnings/failures | `<reported separately; do not relabel as pass>` |

## Deviation, decision, and change safety

| Field | Value |
|---|---|
| Deviation | `<documented source vs observed source, or N/A — reason>` |
| Decision | `<decision required, dependency, assumption, or N/A — reason>` |
| Open item | `<unresolved action, owner, and blocker, or N/A — reason>` |
| Affected slice | `<bounded capability and exact ledger entries>` |
| Preserved contract | `<paths, fields, statuses, invariants, and consumer assumptions>` |
| Rollback | `<application/deployment route-back and last-known-good target>` |
| Stop signal | `<contract, auth, transaction, invariant, history, or quality threshold>` |
| Reconciliation/evidence retention | `<append-only correction and retained logs/audit evidence>` |

## Review outcome

- [ ] Source and observed evidence are both linked where applicable.
- [ ] Classification is explicit and accidental behavior is not promoted.
- [ ] Missing evidence is recorded as a blocker or open item.
- [ ] No historical record, applied migration, API contract, or product
      behavior was changed to make this entry pass.
- [ ] Reviewer approved this entry for the stated baseline revision.
