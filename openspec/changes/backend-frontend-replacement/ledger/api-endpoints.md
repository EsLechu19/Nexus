# API and Consumer Ledger

Baseline revision: `BL-20261021-01`
Source revision: `5ca3881` (working tree also contains pre-existing changes)
Observed at: 2026-10-21 UTC. The route count below is taken from the current
FastAPI application: 19 documented `/api/v1` routes (one public, 18 protected).

The entries record documented contracts and current observations separately.
They do not authorize behavior changes.

| ID | Method and path | Authentication | Request schema | Response schema | Normalization | Status/error | Ordering | Consumer | Classification | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| API-001 | POST `/api/v1/auth/login` | Public | `LoginRequest {email,password}` | `LoginResponse {access_token,token_type}` | email trim/lower; password opaque | 200; 401 `Credenciales inválidas`; missing fields 422 | N/A | `frontend/src/api/auth.js`, `Login.jsx` | documented contract | `specs/011-autenticacion/spec.md`; `app/routers/auth.py:19-47`; auth tests |
| API-002 | POST `/api/v1/productos` | Bearer | `ProductoCreate` | `ProductoResponse` | SKU trim/upper; category trim/lower; optional stock defaults 0 | 201; 409 duplicate SKU; 422 schema | N/A | `frontend/src/api/productos.js` | documented contract | `specs/001-productos-catalogo/spec.md`; router/service tests |
| API-003 | GET `/api/v1/productos` | Bearer | none | `list[ProductoListResponse]` | active products only | 200; 401 auth | SKU ascending observed | `useProductos`, `Productos.jsx` | documented contract / observed behavior | `app/routers/productos.py:39-52`; `test_router_productos_get_list.py` |
| API-004 | GET `/api/v1/productos/{sku}` | Bearer | path SKU | `ProductoResponse` | path trim/upper; includes inactive | 200; 404 not found | N/A | `useProductos` | documented contract | `app/services/producto_service.py:70-79`; detail tests |
| API-005 | PATCH `/api/v1/productos/{sku}` | Bearer | `ProductoUpdate` | `ProductoResponse` | path trim/upper; editable fields trim/lower | 200; 400 inactive/immutable SKU; 404; 422 | N/A | `useProductos` | documented contract | `app/services/producto_service.py:82-118`; patch tests |
| API-006 | DELETE `/api/v1/productos/{sku}` | Bearer | path SKU | `ProductoResponse` | path trim/upper; logical inactive state | 200; 400 already inactive; 404 | N/A | `useProductos` | documented contract | `app/services/producto_service.py:121-138`; delete tests |
| API-007 | POST `/api/v1/proveedores` | Bearer | `ProveedorCreate` | `ProveedorResponse` | code trim/upper; email trim/lower; optional fields preserved/null | 201; 409 duplicate; 422 schema | N/A | `frontend/src/api/proveedores.js` | documented contract | `specs/002-proveedores/spec.md`; supplier router tests |
| API-008 | GET `/api/v1/proveedores` | Bearer | none | `list[ProveedorListResponse]` | active only | 200; 401 auth | code ascending observed | `useProveedores`, `Proveedores.jsx` | documented contract / observed behavior | `app/routers/proveedores.py`; list tests |
| API-009 | GET `/api/v1/proveedores/{codigo}` | Bearer | path code | `ProveedorResponse` | path trim/upper; includes inactive | 200; 404 not found | N/A | `useProveedores` | documented contract | supplier service/detail tests |
| API-010 | PATCH `/api/v1/proveedores/{codigo}` | Bearer | `ProveedorUpdate` | `ProveedorResponse` | path/code trim/upper; email trim/lower | 200; 400 inactive/immutable code; 404; 422 | N/A | `useProveedores` | documented contract | supplier service/patch tests |
| API-011 | DELETE `/api/v1/proveedores/{codigo}` | Bearer | path code | `ProveedorResponse` | path trim/upper; logical inactive state | 200; 400 already inactive; 404 | N/A | `useProveedores` | documented contract | supplier service/delete tests |
| API-012 | POST `/api/v1/movimientos/entradas` | Bearer | `MovimientoCreateEntrada` | `MovimientoResponse` | product/provider codes trim/upper; reason trim | 201; 400 inactive; 404 missing; 422 schema | N/A | `frontend/src/api/movimientos.js`, `Movimientos.jsx` | documented contract | `specs/003-movimientos-inventario/spec.md`; movement tests |
| API-013 | POST `/api/v1/movimientos/salidas` | Bearer | `MovimientoCreateSalida` | `MovimientoResponse` | product code trim/upper; reason trim | 201; 400 inactive/insufficient stock; 404; 422 | N/A | `frontend/src/api/movimientos.js`, `Movimientos.jsx` | documented contract | movement service/router tests |
| API-014 | GET `/api/v1/movimientos` | Bearer | `HistorialQuery` (`producto_codigo`, `tipo`) | `list[MovimientoResponse]` | query code trim/upper | 200; 404 product filter; 422 invalid type | created_at DESC, id DESC | `useMovimientos`, `Movimientos.jsx` | documented contract | `app/services/movimiento_service.py:141-161`; history tests |
| API-015 | GET `/api/v1/stock` | Bearer | none | `list[StockListResponse]` | active products; derived values | 200; 401 auth | SKU/code ascending | `frontend/src/api/stock.js`, `Stock.jsx` | documented contract | `specs/004-consulta-stock/spec.md`; stock tests |
| API-016 | GET `/api/v1/stock/{codigo}` | Bearer | path code | `StockResponse` | code trim/upper | 200; 404 missing or inactive | N/A | `useStock`, `Stock.jsx` | documented contract | stock router/service tests |
| API-017 | POST `/api/v1/ventas` | Bearer | `VentaCreate` (1–20 items) | `VentaResponse` | product codes trim/upper; totals recalculated; duplicate normalized SKU rejected | 201; 400 inactive/insufficient; 404 missing; 422 structure | item order; N/A at collection level | No current frontend consumer; `specs/014-frontend-ventas` is future consumer | documented contract | `specs/012-ventas/spec.md`; `app/routers/ventas.py:70-79`; sales tests |
| API-018 | GET `/api/v1/ventas` | Bearer | none | `list[VentaResponse]` | response timestamps UTC `Z` | 200; 401 auth | created_at DESC, id DESC | Future `014` sales history | documented contract | `app/routers/ventas.py:81-89`; sales GET tests |
| API-019 | GET `/api/v1/ventas/{venta_id}` | Bearer | integer path id | `VentaResponse` | integer path | 200; 404 `Venta no encontrada` | item order by id | Future `014` sales history | documented contract | `app/routers/ventas.py:92-103`; sales GET tests |

## Cross-cutting observations and deviations

- Protected routers declare `Depends(get_current_user)` at router level; current
  tests characterize missing, malformed, invalid-signature, and expired Bearer
  requests as 401 before business access.
- `frontend/src/api/` is the current HTTP ownership boundary. No current
  frontend module consumes the sales endpoints; `014` is explicitly future work.
- The repository README describes 12 protected routes in one summary, while the
  running application exposes 18 protected API routes. This is a **deviation**
  between documentation and observed OpenAPI/application evidence, not a reason
  to change routes.
- `frontend/src/api/movimientos.js` omits an empty `motivo` from payloads; this
  is observed consumer behavior and is not promoted beyond the existing backend
  contract.
- Frontend `lint` and `format` scripts currently echo placeholders. They are
  recorded in `quality-baseline.md` as unavailable gates, not passing quality
  checks.
