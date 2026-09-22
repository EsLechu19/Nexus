# Plan 003 — Movimientos de Inventario

> Constitución: `docs/constitution.md` principios 1-6 | Spec: `specs/003-movimientos-inventario/spec.md` RF-1..RF-4 | Convenciones: `AGENTS.md` | Depende de `001-productos` y `002-proveedores`

## 1. Estructura de módulos afectados

Respetando arquitectura por capas `routers/ → services/ → models/ + schemas/` y principios 1 y 3 (lógica de stock solo en `services`).

| Capa | Archivo | Acción | RF cubiertos | Responsabilidad |
|------|---------|--------|--------------|-----------------|
| `models/` | `app/models/movimiento_inventario.py` | **Modificar** | RF-1, RF-2, RF-3 | Extiende `MovimientoInventario` existente (de `001` con `entrada_inicial`) para soportar `entrada`/`salida` con FKs a `Producto` y `Proveedor` |
| `models/` | `app/models/producto.py` | **Modificar (no esquema)** | RF-1, RF-2, RF-4 | Añadir `stock_actual` derivado no persistido o mantener `stock_inicial` + cálculo; si se persiste, añadir columna `stock_actual` con trigger (descartado, ver §6) |
| `schemas/` | `app/schemas/movimiento.py` | **Crear** | RF-1, RF-2, RF-3, RF-4 | Pydantic `MovimientoCreateEntrada`, `MovimientoCreateSalida`, `MovimientoResponse`, filtros `HistorialQuery`, `StockResponse` |
| `services/` | `app/services/movimiento_service.py` | **Crear** | RF-1..RF-4 | Lógica de negocio: normalización, validación `activo`, cálculo stock, atomicidad y concurrencia |
| `routers/` | `app/routers/movimientos.py` | **Crear** | RF-1..RF-4 | Endpoints REST bajo `/api/v1/movimientos` y `/api/v1/stock`; solo HTTP + delegación |
| `app/` | `app/main.py` | **Modificar** | RF-1..RF-4 | Registrar `movimientos.router` |
| `alembic/` | `alembic/versions/xxxx_movimientos_inventario_003.py` | **Crear** | RF-1, RF-2 | Migración que altera `movimientos_inventario` (ver §8) |

> RF-1 entrada, RF-2 salida, RF-3 historial, RF-4 stock — todos mapeados. Verificación principio 1: `ruff check .`, `mypy app`.

## 2. Modelo de datos

### 2.1 Tabla `movimientos_inventario` (existente de `001`, se altera)
Modelo `MovimientoInventario` → tabla `movimientos_inventario`. Ya existe con `entrada_inicial` de `001`; se extiende para `entrada`/`salida`.

| Columna | Tipo SQLAlchemy/PostgreSQL | Restricciones | Índice | RF |
|---------|----------------------------|---------------|--------|-----|
| `id` | `Integer` PK autoincrement | PK | PK | RF-1, RF-2, RF-3 |
| `producto_id` | `Integer` | `NOT NULL`, `FK productos.id ON DELETE RESTRICT` | `INDEX ix_movimientos_producto_id` + `FK` | RF-1, RF-2 |
| `proveedor_id` | `Integer` | `NULL` ( `NOT NULL` solo para `tipo='entrada'` validado en service, `NULL` para `salida`/`entrada_inicial`), `FK proveedores.id ON DELETE RESTRICT` | `INDEX ix_movimientos_proveedor_id` | RF-1 |
| `tipo` | `VARCHAR(15)` | `NOT NULL`, `CHECK IN ('entrada','salida','entrada_inicial')` | `INDEX ix_movimientos_tipo` | RF-1, RF-2, RF-3 |
| `cantidad` | `Integer` | `NOT NULL`, `CHECK cantidad > 0 AND cantidad <= 1000000` | — | RF-1, RF-2 |
| `motivo` | `VARCHAR(200)` | `NULL`, `CHECK (motivo IS NULL OR length(trim(motivo)) BETWEEN 2 AND 200)` | — | RF-1, RF-2 |
| `created_at` | `DateTime(timezone=True)` | `NOT NULL DEFAULT now()` inmutable | `INDEX ix_movimientos_created_at DESC` | RF-3, RF-4 |

- **FKs:** `producto_id → productos.id` (ya existe, se mantiene `RESTRICT`), `proveedor_id → proveedores.id` (nueva, `RESTRICT`, `NULL` para `salida`). Ambas `ON DELETE RESTRICT` para cumplir principio 5 y RNF-1 (nunca borrar proveedor/producto referenciado).
- **Índices nuevos:** `ix_movimientos_proveedor_id`, `ix_movimientos_tipo`, `ix_movimientos_created_at` (para `RF-3` orden).
- **Checks nuevos:** ampliar `tipo` para incluir `entrada`/`salida` (ya tenía `entrada_inicial`), `proveedor_id` `NOT NULL` condicional se valida en service, no en DB (ver §6).

### 2.2 Tabla `productos` (no se altera esquema, solo lectura de `stock_inicial`)
`productos.stock_inicial` permanece como fuente. `stock_actual` **no se persiste** como columna (ver §6 decisión); se calcula en service. Si se persistiera, se añadiría `stock_actual INTEGER NOT NULL DEFAULT stock_inicial` con trigger, descartado.

### 2.3 Ejemplos de filas representativas

**Entrada (RF-1):**
```json
{
  "id": 15,
  "producto_id": 3,
  "proveedor_id": 2,
  "tipo": "entrada",
  "cantidad": 10,
  "motivo": "Compra semanal",
  "created_at": "2026-09-08T11:00:00Z"
}
```
Corresponde a `POST /api/v1/movimientos/entradas` con `producto="PROD-003"` (`sku` normalizado), `proveedor="PROV-002"`, `cantidad=10`. `stock_actual` del producto pasa de 5 a 15 (`stock_inicial 5 + entradas 10 - salidas 0`).

**Salida (RF-2):**
```json
{
  "id": 16,
  "producto_id": 3,
  "proveedor_id": null,
  "tipo": "salida",
  "cantidad": 8,
  "motivo": "Venta mostrador",
  "created_at": "2026-09-08T12:00:00Z"
}
```
Corresponde a `POST /api/v1/movimientos/salidas` con `producto="PROD-003"`, `cantidad=8`, sin `proveedor`. `stock_actual` pasa de 15 a 7. Si `cantidad` fuera 20 (>7), se rechazaría 400 stock insuficiente (RF-2).

**Entrada inicial (legado 001, RF-4):**
```json
{
  "id": 1,
  "producto_id": 3,
  "proveedor_id": null,
  "tipo": "entrada_inicial",
  "cantidad": 5,
  "motivo": null,
  "created_at": "2026-09-07T10:00:00Z"
}
```
Se muestra en historial (RF-3) pero **no** se suma en `entradas` para `stock_actual` (ver §5 atomicidad).

## 3. Contrato de la API

Base: `/api/v1` (`AGENTS.md`). JSON. Mensajes en español (RNF-2). `codigo` producto/proveedor normalizados `trim+mayúsculas`.

### RF-1 — Registrar entrada `POST /api/v1/movimientos/entradas`

**Request 201:**
```json
POST /api/v1/movimientos/entradas
{
  "producto_codigo": "  prod-003 ",
  "proveedor_codigo": " prov-002 ",
  "cantidad": 10,
  "motivo": "Compra semanal"
}
```
**Response 201:**
```json
{
  "id": 15,
  "producto_codigo": "PROD-003",
  "proveedor_codigo": "PROV-002",
  "tipo": "entrada",
  "cantidad": 10,
  "motivo": "Compra semanal",
  "fecha": "2026-09-08T11:00:00Z",
  "stock_actual": 15
}
```
**Errores:**
- `422` `cantidad` 0/negativa/decimal/>1M, `motivo` `""`/1/201/`\n`, `producto_codigo`/`proveedor_codigo` formato 3-20 → RF-1
- `404` producto no existe, proveedor no existe → RF-1
- `400` producto inactivo, proveedor inactivo → RF-1
- `409` carrera duplicada no aplica (movimientos no tienen unicidad, solo `id`).

### RF-2 — Registrar salida `POST /api/v1/movimientos/salidas`

**Request 201:**
```json
POST /api/v1/movimientos/salidas
{
  "producto_codigo": "PROD-003",
  "cantidad": 8,
  "motivo": "Venta mostrador"
}
```
Si se envía `proveedor_codigo` → `422` (no permitido para salida) o se ignora (decisión: 422 para explicitar, ver §6).

**Response 201:**
```json
{
  "id": 16,
  "producto_codigo": "PROD-003",
  "proveedor_codigo": null,
  "tipo": "salida",
  "cantidad": 8,
  "motivo": "Venta mostrador",
  "fecha": "2026-09-08T12:00:00Z",
  "stock_actual": 7
}
```
**Errores:**
- `422` cantidad/motivo/proveedor no permitido → RF-2
- `404` producto no existe → RF-2
- `400` producto inactivo, stock insuficiente (`cantidad > stock_actual`) → RF-2

### RF-3 — Historial `GET /api/v1/movimientos`

**Request:**
```
GET /api/v1/movimientos
GET /api/v1/movimientos?producto_codigo=PROD-003
GET /api/v1/movimientos?tipo=entrada
GET /api/v1/movimientos?producto_codigo=PROD-003&tipo=salida
```
**Response 200 (orden `fecha DESC, id DESC`):**
```json
[
  {
    "id": 16,
    "producto_codigo": "PROD-003",
    "proveedor_codigo": null,
    "tipo": "salida",
    "cantidad": 8,
    "motivo": "Venta mostrador",
    "fecha": "2026-09-08T12:00:00Z"
  },
  {
    "id": 15,
    "producto_codigo": "PROD-003",
    "proveedor_codigo": "PROV-002",
    "tipo": "entrada",
    "cantidad": 10,
    "motivo": "Compra semanal",
    "fecha": "2026-09-08T11:00:00Z"
  },
  {
    "id": 1,
    "producto_codigo": "PROD-003",
    "proveedor_codigo": null,
    "tipo": "entrada_inicial",
    "cantidad": 5,
    "motivo": null,
    "fecha": "2026-09-07T10:00:00Z"
  }
]
```
**Errores:**
- `404` si `producto_codigo` filtrado no existe → RF-3 (vs `[]` si existe pero sin movimientos)
- `422` si `tipo` no es `entrada`/`salida`/`entrada_inicial` → RF-3
- `200 []` si no hay movimientos → RF-3

### RF-4 — Stock actual `GET /api/v1/stock` y `GET /api/v1/stock/{codigo}`

**Request:**
```
GET /api/v1/stock/PROD-003
GET /api/v1/stock
GET /api/v1/stock?incluir_inactivos=true
```
**Response 200 por producto:**
```json
{
  "codigo": "PROD-003",
  "nombre": "PlayStation 5 Slim",
  "stock_inicial": 5,
  "entradas": 10,
  "salidas": 8,
  "stock_actual": 7
}
```
`entradas` suma solo `tipo='entrada'`, `salidas` suma `salida`, `entrada_inicial` no suma (se informa aparte si se quiere: `entradas_iniciales: 5`).

**Response 200 global (solo activos por defecto):**
```json
[
  {"codigo":"PROD-001","nombre":"Juego A","stock_inicial":0,"entradas":0,"salidas":0,"stock_actual":0},
  {"codigo":"PROD-003","nombre":"PlayStation 5 Slim","stock_inicial":5,"entradas":10,"salidas":8,"stock_actual":7}
]
```
Ordenado por `codigo`. Inactivos solo con `?incluir_inactivos=true`.

**Errores:**
- `404` si `codigo` no existe → RF-4

**Resumen códigos:**

| Endpoint | 200 | 201 | 400 | 404 | 422 |
|----------|-----|-----|-----|-----|-----|
| POST /movimientos/entradas |  | RF-1 | RF-1 proveedor/producto inactivo, stock insuficiente no aplica | RF-1 no existe |  | RF-1 validación |
| POST /movimientos/salidas |  | RF-2 | RF-2 producto inactivo, stock insuficiente | RF-2 no existe |  | RF-2 validación / proveedor enviado |
| GET /movimientos | RF-3 |  |  | RF-3 producto filtro no existe |  | RF-3 tipo inválido |
| GET /stock/{codigo} | RF-4 |  |  | RF-4 |  |  |
| GET /stock | RF-4 |  |  |  |  |  |

## 4. Reglas de validación: schema vs service

**Principio 3:** `routers/` solo HTTP, `schemas/` solo sintaxis, `services/` solo negocio.

**En `schemas/movimiento.py` (Pydantic) — RF-1, RF-2, RF-3 (sintáctica, sin I/O, 422):**
- `producto_codigo`/`proveedor_codigo` `trim+mayúsculas` `^[A-Z0-9_-]{3,20}$`, requeridos (proveedor solo para entrada); `cantidad` `StrictInt` `1..1_000_000`, rechazo `0`/negativa/decimal/`>1M`/`"10"`; `motivo` `Optional` `trim` 2-200, `null`/ausente → `None`, `""`/`1`/`201`/`\n` → 422; `proveedor_codigo` enviado en salida → 422 (no permitido).
- `tipo` filtro `entrada`/`salida`/`entrada_inicial` para `GET /movimientos`.
- Justificación: declarativas, sin I/O, baratas, 422 inmediato; Pydantic canónico (`AGENTS.md`).

**En `services/movimiento_service.py` — negocio con BD, 404/400 (RF-1..RF-4):**
- RF-1: `producto` existe y `estado==activo` → 404/400; `proveedor` existe y `activo` → 404/400; normalización `trim+upper` ya hecha pero se revalida; `proveedor` `null` para `entrada` → 422.
- RF-2: `producto` `activo` → 404/400; `stock_actual >= cantidad` verificado con `SELECT FOR UPDATE` del producto (ver §6); `proveedor` enviado → 400/422 según decisión.
- RF-3/RF-4: `producto_codigo` filtro no existe → 404; `stock_actual` recalculado `inicial + SUM(entrada) - SUM(salida)` (excluye `entrada_inicial`); `proveedor` inactivo en historial se conserva pero no se valida.
- Justificación: requieren estado persistido, cálculo de stock y transacción; no pertenecen a `schema` (principio 5, RNF-3).

## 5. Atomicidad de la transacción

**Garantía:** `INSERT movimiento` + `SELECT SUM`/`UPDATE` implícito de `stock_actual` (si se persistiera) deben ser atómicos: o ambos ocurren o ninguno.

**Implementación (RF-1, RF-2):**
- Una transacción `BEGIN` por registro: `SELECT ... FOR UPDATE` del `producto` (bloquea fila), `SELECT SUM` de movimientos del producto para calcular `stock_actual` actual, validación `stock_actual >= cantidad` para `salida`, `INSERT` del movimiento, `COMMIT`. Si `stock_actual` se persistiera en `productos.stock_actual`, se haría `UPDATE productos SET stock_actual = stock_actual + cantidad` dentro de la misma transacción; como no se persiste (ver §6), el `INSERT` solo es suficiente y el cálculo en `RF-4` lo refleja, pero la transacción sigue garantizando que el `SELECT FOR UPDATE` y el `INSERT` son atómicos.
- Uso de `Session` con `autocommit=False`, `try: ... commit() except: rollback()`. `IntegrityError` no esperado para movimientos (sin unicidad), pero se captura para `id`.
- Aislamiento: `READ COMMITTED` por defecto en PostgreSQL es suficiente con `FOR UPDATE`; `REPEATABLE READ` no necesario.
- RF cubiertos: RF-1, RF-2 (escritura), RF-4 (lectura consistente).

**Alternativa descartada:** Dos transacciones separadas (`INSERT` luego `UPDATE`) — dejaría ventana donde `stock_actual` no refleja el movimiento, violando RNF-3 y dejando stock inconsistente si falla la segunda.

## 6. Estrategia de concurrencia: pesimista vs optimista

**Problema (RF-2):** Dos `salida` concurrentes con `stock_actual=10` cada una `cantidad=8` individualmente pasarían `stock >= cantidad`, pero juntas dejarían `stock=-6`.

**Elegida: Locking pesimista `SELECT ... FOR UPDATE` del `producto` (RF-1, RF-2)**
- Al registrar `entrada`/`salida`, se hace `SELECT * FROM productos WHERE id=:id FOR UPDATE` dentro de la transacción. La segunda transacción espera a que la primera haga `COMMIT` y luego recalcula `stock_actual` ya actualizado, viendo `stock=2` y rechazando la segunda `salida` con `400 stock insuficiente` (RNF-3).
- Justificación: `producto` es hotspot de contención pero cardinalidad baja (un producto a la vez), `FOR UPDATE` es simple, correcto y evita `stock<0` sin lógica de reintento; PostgreSQL lo soporta nativamente y es el patrón recomendado para contadores.

**Descartada: Locking optimista con columna `version` en `productos`**
- Requeriría añadir `version INTEGER NOT NULL DEFAULT 0`, incrementarla en cada movimiento y detectar `StaleDataError` → `409` y reintentar. Ventaja: sin bloqueos, más throughput para alta contención.
- Descartada porque añade complejidad (columna extra, manejo de reintentos en service y router → 409), y para inventario el throughput no justifica el costo; el bloqueo pesimista es más simple y garantiza RNF-3 sin reintentos visibles al cliente (solo espera de lock). Se evaluará si la contención supera 10 TPS por producto.

**Pruebas de concurrencia (RF-2):** Test unitario con `ThreadPoolExecutor` (2 hilos) + `sqlite:///:memory:` con `FOR UPDATE` simulado o `PostgreSQL` `testcontainers`, y test de integración que lanza dos `POST /salidas` concurrentes con `httpx.AsyncClient`.

## 7. Decisiones técnicas adicionales

1. **`stock_actual` no persistido vs columna `productos.stock_actual`**
   - Elegida: no persistir, calcular en cada `GET /stock` como `stock_inicial + SUM(entrada) - SUM(salida)` (excluye `entrada_inicial`).
   - Descartada: `stock_actual` persistido con `UPDATE` en cada movimiento.
   - Motivo: evita divergencia entre columna y movimientos (fuente append-only), simplifica atomicidad (solo `INSERT`), y es suficiente para volumen MVP (<10k movimientos/producto); se puede materializar con vista materializada si escala.

2. **`tipo` `VARCHAR + CHECK` vs `PostgreSQL ENUM`**
   - Elegida: `VARCHAR(15)` `CHECK IN ('entrada','salida','entrada_inicial')`.
   - Descartada: `ENUM` nativo.
   - Motivo: más fácil de migrar con Alembic y añadir `ajuste` futuro sin `ALTER TYPE`; historial no es cerrado.

3. **`proveedor_id` `NULL` para `salida` vs tabla separada `entradas`/`salidas`**
   - Elegida: columna `proveedor_id` `NULLABLE` con `CHECK (tipo='entrada' AND proveedor_id IS NOT NULL OR tipo!='entrada')`.
   - Descartada: dos tablas o `salida` con `proveedor_id` `NOT NULL`.
   - Motivo: unifica historial (`RF-3`) en una sola tabla, simplifica `ORDER BY fecha`, y `salida` no necesita proveedor (RF-2).

4. **`motivo` `NULL` vs `""`**
   - Elegida: `NULL` para `null`/ausente, `""` → 422.
   - Descartada: `""` como `NULL`.
   - Motivo: distingue “sin motivo” vs “motivo vacío” (caso límite `spec.md:63`), coherente con `002` proveedores.

5. **`historial` sin paginación vs paginado**
   - Elegida: sin paginación (devuelve todo) orden `fecha DESC, id DESC`.
   - Descartada: paginación `limit/offset`.
   - Motivo: `spec.md:72` fuera de alcance paginación en MVP; volumen esperado <1k movimientos/producto; se añadirá `?limit&offset` sin breaking change.

6. **`POST /movimientos/entradas` y `/salidas` separados vs `POST /movimientos` con `tipo` en body**
   - Elegida: dos endpoints separados.
   - Descartada: uno genérico con `tipo` en JSON.
   - Motivo: hace obligatorio `proveedor` solo para `entrada` a nivel de schema (discriminated union), da 422 claro si `proveedor` falta en entrada o se envía en salida, y alinea con `spec.md:18`/`27`.

7. **`proveedor_codigo` en API vs `proveedor_id`**
   - Elegida: API expone `codigo` (`PROV-001`), interno mapea a `id` para FK.
   - Descartada: exponer `id` directamente.
   - Motivo: `codigo` es identificador de negocio estable y normalizado, `id` es interno; `spec.md:18` define `codigo` como identificador de negocio, `plan 002 §2.3` expone `id` para FK.

## 8. Plan de migración Alembic

**Revisión:** `alembic revision --autogenerate -m "extiende movimientos inventario 003"` → `alembic upgrade head` sin errores (principio 5).

**Cambios sobre `movimientos_inventario` existente (de `001`):**
- Alterar columna `proveedor_id`: añadir `ForeignKey("proveedores.id", ondelete="RESTRICT")`, `nullable=True`, `index=True` (si no existe).
- Alterar `tipo`: `VARCHAR(15)` → `VARCHAR(15)` con `CHECK IN ('entrada','salida','entrada_inicial')` (ampliar de solo `entrada_inicial`).
- Añadir `motivo` `VARCHAR(200) NULL` con `CHECK (motivo IS NULL OR length(trim(motivo)) BETWEEN 2 AND 200)`.
- Índices nuevos: `ix_movimientos_tipo`, `ix_movimientos_created_at` (`fecha`).
- No toca `productos` ni `proveedores` (ya en `37840112ca70`); si se decide persistir `stock_actual`, se añadiría columna pero descartado.
- Verificación: `alembic upgrade head` y `downgrade -1` + `upgrade` sin pérdida; `INSERT` con `proveedor_id NULL` para `salida` debe pasar, con `NOT NULL` para `entrada` debe fallar si service no valida (pero service valida).

## 9. Estrategia de tests

Sin escribir código de tests (principio 4: `pytest -v` verde).

**Unitarios — `services/movimiento_service.py` (mock `Session` / `sqlite:///:memory:` con `Base.metadata.create_all`):**
- RF-1: entrada válida `producto`/`proveedor` activos `cantidad` 1/1M → crea `entrada`; `producto`/`proveedor` no existe/inactivo → 404/400; `cantidad` 0/negativa/decimal/`>1M` → 422; `motivo` `""`/1/201/`\n` → 422, `null`/ausente → crea sin motivo; concurrencia `proveedor` que pasa a `inactivo` entre `SELECT` y `INSERT` → 400 por `FOR UPDATE`.
- RF-2: salida válida con `stock_actual >= cantidad` → crea `salida`; `producto` no existe/inactivo → 404/400; `proveedor` enviado → 422; `stock_insuficiente` (`cantidad > stock_actual`) → 400 sin `INSERT`; `stock_actual == cantidad` → deja 0; `motivo` igual que RF-1.
- RF-2 concurrencia: dos hilos `salida` con `stock 10` cada una `8` → una `200` otra `400` (pesimista), verificado con `ThreadPoolExecutor` y `SELECT FOR UPDATE` mock.
- RF-3/RF-4: `listar_historial` filtra por `producto`/`tipo`, orden `fecha DESC, id DESC`, `producto` inexistente → 404 vs `[]`; `calcular_stock` `stock_inicial + entradas - salidas` excluyendo `entrada_inicial`, `stock_inicial` solo → `stock_actual == inicial`.

**Integración — `routers/movimientos.py` + `routers/stock.py` (`TestClient` + `TestSession` con `productos`/`proveedores` creados via `POST` previos):**
- RF-1: `POST /api/v1/movimientos/entradas` `201` con `proveedor` normalizado, `409` no aplica, `404`/`400`/`422` como arriba, verifica `proveedor_id` en DB y `stock_actual` incrementado.
- RF-2: `POST /api/v1/movimientos/salidas` `201`, `400` stock insuficiente, `422` `proveedor` enviado, `404`/`400` producto.
- RF-3: `GET /api/v1/movimientos` `200` `[]` vacío y con datos ordenados, `?producto_codigo=PROD-001` `200` filtrado, `?tipo=entrada` `200`, `404` producto filtro no existe, `422` tipo inválido.
- RF-4: `GET /api/v1/stock/{codigo}` `200` con `entradas/salidas/stock_actual`, `404` no existe, `GET /api/v1/stock` `200` solo activos ordenados, `?incluir_inactivos=true` incluye `inactivos`; verifica `stock_actual` no expone `id`/`fecha` internos y mensajes en español.
- Transversal: sin `UPDATE`/`DELETE` sobre `movimientos_inventario` (verificar que `PUT/PATCH/DELETE /movimientos` no existen), `ruff`/`mypy` pasan, `GET /docs` lista 4 endpoints nuevos.

Cada test mapea a su RF y RNF-1..RNF-5.
