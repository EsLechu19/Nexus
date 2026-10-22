# Baseline Contract Ledger

This directory contains the versioned evidence ledger for the incremental
backend and frontend replacement. It records current facts before any
replacement slice changes implementation. It does not define new business
behavior and it never converts accidental behavior into a desired contract.

## Baseline revision convention

Every reviewed snapshot uses `BL-YYYYMMDD-NN`, where:

- `YYYYMMDD` is the UTC date on which the snapshot is frozen.
- `NN` is a two-digit sequence for additional snapshots on the same date,
  starting at `01`.
- The revision is immutable after review. Corrections create the next revision
  and link back to the superseded revision.
- A ledger entry records its source revision and its observed-at revision (Git
  commit, tag, or explicit `working-tree` marker when no commit is available).

The first baseline is not approved by this template task. Use the next
available identifier only after the evidence inventory and release gate have
been reviewed.

## Evidence classifications

Each assertion in an entry has exactly one classification:

- `documented contract` — behavior required by an existing specification or
  approved decision.
- `observed behavior` — behavior demonstrated by source, a fixture, or a
  runtime check without being promoted to a requirement.
- `deviation` — an observed/documented mismatch; preserve both sources.
- `assumption` — an unverified premise required to interpret the evidence.
- `dependency` — an external prerequisite, tool, environment, or owner.
- `open decision` — an unresolved choice that blocks or constrains later work.

An observed behavior must not be labeled `documented contract` solely because
an existing consumer depends on it. Deviations, assumptions, dependencies, and
open decisions remain visible until a named review resolves them.

## How to use the template

Copy `entry-template.md` for each endpoint, data invariant, quality command,
deviation, decision, or bounded replacement slice. Keep source evidence and
runtime evidence separate, record failures as evidence, and link every later
slice to the approved baseline revision and its rollback target.

Run `tests/test_T0_001_ledger_template.py` after changing the template. This
check validates the minimum reusable structure; it does not claim that the
ledger has been populated or approved.
