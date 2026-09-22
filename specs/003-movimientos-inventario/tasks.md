# Tasks 003 — Movimientos de Inventario

> Orden por dependencias. Cada tarea 20-30 min. Constitución y `AGENTS.md` vigentes.

- [x] **T01 — Modelo `MovimientoInventario` (extiende tabla `movimientos_inventario`)** — RF-1, RF-2, RF-3
  - RF: RF-1 (entrada), RF-2 (salida), RF-3 (historial)
  - Hecho cuando: `app/models/movimiento_inventario.py` define `MovimientoInventario` con `id, producto_id FK productos.id RESTRICT, proveedor_id FK proveedores.id RESTRICT NULL (NOT NULL solo para entrada validado en service), tipo VARCHAR(15) CHECK IN ('entrada','salida','entrada_inicial'), cantidad INTEGER CHECK 1..1_000_000, motivo VARCHAR(200) NULL CHECK 2-200 o NULL, created_at`, índices `ix_movimientos_producto_id, ix_movimientos_proveedor_id, ix_movimientos_tipo, ix_movimientos_created_at DESC`, y `mypy app` pasa.

- [x] **T02 — Schemas Pydantic `MovimientoCreateEntrada / MovimientoCreateSalida / MovimientoResponse / HistorialQuery / StockResponse`** — RF-1, RF-2, RF-3, RF-4
  - RF: RF-1, RF-2, RF-3, RF-4
  - Hecho cuando: `app/schemas/movimiento.py` valida `producto_codigo`/`proveedor_codigo` 3-20 regex trim+upper, `cantidad` StrictInt 1..1_000_000, `motivo` 2-200 trim sin `\n` (`null`/ausente -> None, `""` -> 422), `proveedor_codigo` requerido solo para entrada y prohibido para salida (422), `tipo` filtro `entrada`/`salida`/`entrada_inicial`, y `ruff check .` pasa.

- [x] **T03 — Service: registrar `entrada` con `proveedor` activo y stock** — RF-1
  - RF: RF-1
  - Hecho cuando: `app/services/movimiento_service.py:registrar_entrada` normaliza `producto_codigo`/`proveedor_codigo` trim+upper, valida `producto`/`proveedor` existen y `activo` (404/400) con `SELECT FOR UPDATE` del producto, crea `Movimiento` `entrada` en transacción atómica, retorna con `stock_actual` recalculado, y `mypy app` pasa.

- [x] **T04 — Service: registrar `salida` con validación de stock insuficiente** — RF-2
  - RF: RF-2
  - Hecho cuando: `registrar_salida` normaliza `producto_codigo`, valida `producto` activo (404/400), verifica `stock_actual >= cantidad` con `SELECT FOR UPDATE`, rechaza 400 stock insuficiente sin `INSERT`, ignora `proveedor` si se envía (422), crea `salida` con `proveedor_id=NULL` y `motivo` opcional.

- [x] **T05 — Service: consultas `listar_historial()` y `calcular_stock()`** — RF-3, RF-4
  - RF: RF-3, RF-4
  - Hecho cuando: `listar_historial(producto_codigo?, tipo?)` filtra por `codigo` normalizado y `tipo`, ordena `created_at DESC, id DESC`, devuelve `[]` si vacío o 404 si `producto` filtro no existe, y `calcular_stock(codigo)` / `listar_stock()` recalculan `stock_inicial + entradas - salidas` (excluye `entrada_inicial` del doble conteo) y retornan `entradas/salidas/stock_actual`.

- [x] **T06 — Router `POST /api/v1/movimientos/entradas`** — RF-1
  - RF: RF-1
  - Hecho cuando: `app/routers/movimientos.py` expone `POST` que delega a `registrar_entrada`, retorna 201 con `id/proveedor_codigo/tipo/cantidad/motivo/fecha/stock_actual`, 404/400 según service, 422 validación, sin lógica de negocio en router.

- [x] **T07 — Router `POST /api/v1/movimientos/salidas`** — RF-2
  - RF: RF-2
  - Hecho cuando: `POST /salidas` delega a `registrar_salida`, retorna 201 con `proveedor_codigo=null`, 400 stock insuficiente, 404/422 según service, sin `proveedor` permitido.

- [x] **T08 — Router `GET /api/v1/movimientos` historial** — RF-3
  - RF: RF-3
  - Hecho cuando: `GET` con `?producto_codigo&tipo` filtra, ordena `fecha DESC`, retorna 200 con `id/producto/proveedor/tipo/cantidad/motivo/fecha` o `[]`, 404 producto no existe, 422 tipo inválido, delega a `listar_historial`.

- [x] **T09 — Router `GET /api/v1/stock` y `GET /api/v1/stock/{codigo}`** — RF-4
  - RF: RF-4
  - Hecho cuando: `GET /stock/{codigo}` retorna 200 con `codigo/nombre/stock_inicial/entradas/salidas/stock_actual` (incluye `inactivo` si se consulta por código), `GET /stock` lista solo `activos` ordenados por `codigo` (con `?incluir_inactivos=true` incluye todos), 404 si producto no existe, delega a `calcular_stock`.

- [x] **T10 — Registro de routers en `app/main.py`** — RF-1..RF-4
  - RF: RF-1, RF-2, RF-3, RF-4
  - Hecho cuando: `app/main.py` incluye `movimientos.router` y `stock.router` (o único router con prefijos `/movimientos` y `/stock`) y `GET /openapi.json` lista 4 endpoints nuevos (2 POST + 2 GET) además de los 10 previos (total 14) y `GET /docs` 200.

- [x] **T11 — Migración Alembic `extiende movimientos inventario 003`** — RF-1, RF-2
  - RF: RF-1, RF-2
  - Hecho cuando: `alembic revision --autogenerate -m "extiende movimientos inventario 003"` genera migración que añade `proveedor_id` FK, `motivo`, amplía `tipo` CHECK y añade índices, y `alembic upgrade head` y `downgrade -1` + `upgrade` pasan sin errores.

- [x] **T12 — Tests unitarios de service (mock + sqlite, concurrencia)** — RF-1..RF-4
  - RF: RF-1, RF-2, RF-3, RF-4
  - Hecho cuando: tests cubren entrada con/sin motivo y proveedor normalizado, salida con stock suficiente/insuficiente, `cantidad` 0/negativa/decimal/>1M, `motivo` `""`/1/201/`\n`, `producto`/`proveedor` no existe/inactivo, `proveedor` enviado en salida, historial filtrado y orden, `stock_actual` recalculado, y concurrencia con `ThreadPoolExecutor` 2 salidas que exceden stock (una 201 otra 400) con `SELECT FOR UPDATE` mock; `pytest -v` unitarios en verde y `mypy app` pasa.

- [x] **T13 — Tests de integración de endpoints (TestClient + DB test)** — RF-1..RF-4
  - RF: RF-1, RF-2, RF-3, RF-4
  - Hecho cuando: `POST /movimientos/entradas` 201 + stock incrementado, `POST /salidas` 201 y 400 stock insuficiente, `GET /movimientos` filtra por producto/tipo y orden, `GET /stock` lista solo activos y detalle incluye `inactivo`, `proveedor` null para salida, mensajes en español y sin exponer modelos; `pytest -v` integración en verde.

- [x] **T14 — Verificación final constitución + AGENTS.md** — RF-1..RF-4
  - RF: RF-1, RF-2, RF-3, RF-4
  - Hecho cuando: `pytest -v` 100% verde, `ruff check .` y `ruff format .` sin errores, `mypy app` sin errores, `alembic upgrade head` ok, `GET /docs` lista 14 endpoints y `stock_actual` nunca negativo.
