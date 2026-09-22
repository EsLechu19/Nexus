# Tasks 001 — Catálogo de Productos

> Orden por dependencias. Cada tarea 20-30 min. Constitución y `AGENTS.md` vigentes.

- [x] **T01 — Crear estructura base y rama** — RF: — 
  - RF: ninguno (infra)
  - Hecho cuando: existen `app/models/`, `app/schemas/`, `app/services/`, `app/routers/` y rama `001-productos-catalogo` creada.

- [x] **T02 — Modelo `Producto` (tabla `productos`)** — RF-1, RF-4, RF-5
  - RF: RF-1 (definición), RF-4 (campos editables), RF-5 (estado)
  - Hecho cuando: `app/models/producto.py` define `Producto` con columnas `id, sku VARCHAR(20) UNIQUE, nombre VARCHAR(100), categoria, stock_inicial, estado, created_at, updated_at`, checks e índices según plan §2.1, y `mypy app` pasa.

- [x] **T03 — Modelo `MovimientoInventario` (tabla `movimientos_inventario`)** — RF-1
  - RF: RF-1 (traza inicial)
  - Hecho cuando: `app/models/movimiento_inventario.py` define `MovimientoInventario` con `producto_id FK RESTRICT, tipo='entrada_inicial', cantidad, created_at`, append-only, y `mypy app` pasa.

- [x] **T04 — Schemas Pydantic `ProductoCreate / ProductoUpdate / ProductoResponse`** — RF-1, RF-4
  - RF: RF-1, RF-4
  - Hecho cuando: `app/schemas/producto.py` valida `nombre 2-100 trim`, `sku 3-20 regex`, `categoria enum`, `stock_inicial int 0-1M opcional`, `ProductoUpdate` exige ≥1 campo, y `ruff check .` pasa.

- [x] **T05 — Service: alta `crear_producto()` con normalización y unicidad** — RF-1
  - RF: RF-1
  - Hecho cuando: `app/services/producto_service.py:crear_producto` normaliza `sku trim+upper`/`categoria trim+lower`, rechaza duplicado incluyendo inactivos (409), valida rangos, crea producto `activo` y si `stock_inicial>0` crea traza en misma transacción; captura `IntegrityError` → 409.

- [x] **T06 — Service: consultas `listar_activos()` y `obtener_por_sku()`** — RF-2, RF-3
  - RF: RF-2, RF-3
  - Hecho cuando: service devuelve solo `activos` con `sku,nombre,categoria,stock_inicial` (RF-2) y detalle con `estado` incluyendo inactivos usando SKU normalizado (RF-3); 404 si no existe.

- [x] **T07 — Service: edición `actualizar_producto()`** — RF-4
  - RF: RF-4
  - Hecho cuando: service edita solo `nombre`/`categoria` de producto `activo`, rechaza 404 no encontrado, 400 inactivo, 400 validación, 400 `sku` distinto inmutable (mismo valor se ignora), y ignora `stock_inicial`/`estado` extra.

- [x] **T08 — Service: baja lógica `baja_producto()`** — RF-5
  - RF: RF-5
  - Hecho cuando: service marca `activo→inactivo`, rechaza 404 no encontrado y 400 ya inactivo, permite con cualquier `stock_inicial`, sin `DELETE` físico.

- [x] **T09 — Router `POST /api/v1/productos`** — RF-1
  - RF: RF-1
  - Hecho cuando: `app/routers/productos.py` expone `POST` que delega a service, retorna 201 con `sku` normalizado, 400/422 validación Pydantic, 409 duplicado, sin lógica de negocio en router.

- [x] **T10 — Router `GET /api/v1/productos` listado** — RF-2
  - RF: RF-2
  - Hecho cuando: `GET` retorna 200 con lista de activos o `[]` si vacío, excluye inactivos, delega a service.

- [x] **T11 — Router `GET /api/v1/productos/{sku}` detalle** — RF-3
  - RF: RF-3
  - Hecho cuando: `GET` con `{sku}` normalizado retorna 200 activo/inactivo completo, 404 si no existe, delega a service.

- [x] **T12 — Router `PATCH /api/v1/productos/{sku}` edición** — RF-4
  - RF: RF-4
  - Hecho cuando: `PATCH` retorna 200 tras editar, 404/400 según service, valida al menos un campo, y `/docs` muestra schema correcto.

- [x] **T13 — Router `DELETE /api/v1/productos/{sku}` baja lógica** — RF-5
  - RF: RF-5
  - Hecho cuando: `DELETE` retorna 200 con `estado=inactivo`, 404/400 según service, y posterior `GET` listado no lo incluye pero detalle sí.

- [x] **T14 — Registro del router en `app/main.py`** — RF-1..RF-5
  - RF: RF-1, RF-2, RF-3, RF-4, RF-5
  - Hecho cuando: `app/main.py` incluye `productos.router` bajo prefijo `/api/v1` y `GET /docs` lista los 5 endpoints.

- [x] **T15 — Migración Alembic `crea catalogo productos`** — RF-1, RF-5
  - RF: RF-1, RF-5
  - Hecho cuando: `alembic revision --autogenerate -m "crea catalogo productos"` genera `xxxx_crea_catalogo_productos.py` con ambas tablas/checks/índices y `alembic upgrade head` y `downgrade -1` + `upgrade` pasan sin errores.

- [x] **T16 — Tests unitarios de service (mock session)** — RF-1..RF-5
  - RF: RF-1, RF-2, RF-3, RF-4, RF-5
  - Hecho cuando: tests cubren alta válida/duplicado normalizado/validaciones, edición inmutable/inactivo, baja idempotencia, consultas filtradas y carrera `IntegrityError`; `pytest -v` unitarios en verde.

- [x] **T17 — Tests de integración de endpoints (TestClient + DB test)** — RF-1..RF-5
  - RF: RF-1, RF-2, RF-3, RF-4, RF-5
  - Hecho cuando: `POST/GET/PATCH/DELETE /api/v1/productos` verifican 201/200/400/404/409, traza inicial creada solo si `>0`, inactivo excluido de listado pero visible en detalle, mensajes en español y sin exponer modelos; `pytest -v` integración en verde.

- [x] **T18 — Verificación final constitución + AGENTS.md** — RF-1..RF-5
  - RF: RF-1, RF-2, RF-3, RF-4, RF-5
  - Hecho cuando: `pytest -v` 100% verde, `ruff check .` y `ruff format .` sin errores, `mypy app` sin errores, `alembic upgrade head` ok y `GET /docs` responde para los 5 endpoints.
