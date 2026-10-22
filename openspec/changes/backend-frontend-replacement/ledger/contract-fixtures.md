# Representative Contract Fixtures

Baseline revision: `BL-20261021-01`; source revision `5ca3881`.
These are characterization fixtures, not new requirements or production data.
They preserve documented and observed classifications for later comparisons.

## Authentication

| Case | Request/condition | Observed result | Classification | Evidence |
|---|---|---|---|---|
| success | `POST /auth/login` with ` admin@tienda.com ` and valid password | 200; `access_token`; `token_type=bearer` | documented contract | `tests/test_auth_login_T06_011.py` |
| missing fields | `{}` | 422 validation body | documented contract | auth schema tests |
| invalid credentials | valid shape, unknown email/password | 401 `Credenciales inválidas` | documented contract | auth login tests |
| protected without token | `GET /productos` no Authorization | 401 before business/database access | documented contract | protection tests |
| expired token | protected request with expired JWT | 401 | documented contract | JWT/dependency tests |

## Catalog and suppliers

| Capability | Success fixture | Validation/not-found/conflict fixture | Expected evidence |
|---|---|---|---|
| products | create `{"sku":" ab-1 ","nombre":"Juego","categoria":" VIDEOJUEGO ","stock_inicial":5}` → 201, SKU `AB-1` | duplicate normalized SKU → 409; missing product → 404; invalid shape → 422 | product router/service/schema tests |
| suppliers | create `{"codigo":" prov-1 ","nombre":"Proveedor","email":" A@EXAMPLE.COM "}` → 201, code/email normalized | duplicate code → 409; inactive edit → 400; invalid email → 422 | supplier integration/router/schema tests |

## Inventory and stock

| Case | Fixture | Expected result | Classification |
|---|---|---|---|
| initial stock | product stock_initial 5 | stock response has initial 5, entries 0, exits 0, actual 5 | documented contract |
| entry | active product/provider, quantity 3 | 201 and actual 8; movement has type `entrada` | documented contract |
| exit | active product, quantity 2 | 201 and actual 6; movement has type `salida` | documented contract |
| insufficient exit | quantity greater than actual | 400 `Stock insuficiente`, no accepted movement | documented contract |
| history filter | product code with `tipo=entrada` | created_at DESC then id DESC | documented contract |
| low stock | minimum > 0 and actual < minimum | `alerta=true`; zero minimum never alerts | documented contract |

## Sales

| Case | Fixture | Expected result | Classification |
|---|---|---|---|
| successful sale | two active products with sufficient stock, 2 items | 201; recalculated total; one movement id per item; linked rows | documented contract |
| malformed sale | empty/21-item cart, duplicate normalized SKU, decimal quantity | 422; no writes | documented contract |
| missing/inactive product | item references missing/inactive SKU | 404/400 respectively; no sale or movement partial write | documented contract |
| insufficient stock | one item exceeds available stock | 400 with available/requested diagnostics; rollback leaves no sale/movement | documented contract |
| history | two sales | list ordered created_at DESC, id DESC; detail 404 for unknown id | documented contract |

## Source and retention

The executable evidence is retained in the existing tests, especially
`test_venta_atomicidad_T05_012.py`, `test_ventas_post_T06_012.py`,
`test_integracion_movimientos_T13.py`, auth/protection tests, and frontend API
tests. Any mismatch found by a later replacement is recorded as a deviation or
reconciliation blocker; fixtures never repair, delete, or update historical data.
