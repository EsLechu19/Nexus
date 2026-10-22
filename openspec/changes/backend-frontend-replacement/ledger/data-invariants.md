# Persistence, Migration, and Historical Invariants

Baseline revision: `BL-20261021-01`; observed at 2026-10-21 UTC; source
revision `5ca3881`. This inventory describes the current SQLAlchemy metadata and
Alembic history. No migration or record was edited by Phase 0.

## Compatibility-critical schema

| Table | Columns and constraints | Relationships / historical rule |
|---|---|---|
| `usuarios` | `id` PK, `email` varchar(254) unique, `password_hash` varchar(72), `created_at` timestamp | Credentials are not API response fields; password hashes are never exposed |
| `productos` | `id` PK, `sku` varchar(20) unique, `nombre`, `categoria`, `stock_inicial`, `stock_minimo`, `estado`, `created_at`, `updated_at`; checks for ranges/enums | Referenced by movements, sale items; logical inactive state, no physical deletion in service behavior |
| `proveedores` | `id` PK, unique `codigo`, `nombre`, nullable email/phone/address, `estado`, timestamps; length/format checks | Referenced by entry movements with RESTRICT FK |
| `movimientos_inventario` | `id` PK, `producto_id`, nullable `proveedor_id`, `tipo`, positive `cantidad`, optional `motivo`, `created_at` | Product/provider FKs use `ON DELETE RESTRICT`; append-only evidence; entry requires provider |
| `ventas` | `id` PK, `created_at`, embedded client name/email, non-negative numeric `total` | Sale header is append-only evidence |
| `venta_items` | `id` PK, `venta_id`, `producto_id`, quantity, unit price, subtotal, nullable `movimiento_id` with unique index | FKs use RESTRICT; one movement link per item; sale traceability |

## Migration chain

Applied head: `2c3245f4f658`. Current linear revisions:

1. `1a81a5e6e75b` — catalog products
2. `63276eeea69c` — inventory movements
3. `37840112ca70` — suppliers
4. `9111dba96a53` — movement extensions
5. `7010b4ddca09` — product minimum stock
6. `ff5b41c7a385` — users
7. `2c3245f4f658` — sales and sale items

Evidence: `alembic heads`, `alembic history --verbose`, `alembic upgrade head`,
`alembic.ini`, and `alembic/versions/*.py`. Applied revisions are protected;
future schema changes require a new additive forward-only revision.

## Invariants

- Stock is derived as `stock_actual = stock_inicial + entradas - salidas`.
  Entries and exits are positive movements; service tests verify non-negative
  stock and exact/insufficient exit behavior.
- `movimientos_inventario`, `ventas`, and `venta_items` are append-only
  historical evidence. There is no update/delete service path for these records;
  foreign keys use RESTRICT to preserve links.
- A successful sale creates one sale, its items, and one linked exit movement per
  item in the authoritative current service operation. Failure validation is
  characterized to leave no accepted partial sale or movement.
- Existing identifiers, timestamps, quantities, prices, totals, and movement
  links must remain readable and unchanged. Baseline found no mismatch requiring
  repair; PostgreSQL concurrency rehearsal remains an open decision.

## Open persistence decisions

- PostgreSQL is the documented production stack, while local tests and current
  Alembic evidence use SQLite. Owner: maintainer; decide before concurrency or
  migration-rehearsal claims.
- Production row counts/checksums were not available in this local baseline.
  Owner: deployment/data owner; provide before a persistence cutover.
