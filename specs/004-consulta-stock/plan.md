# Plan 004 — Consulta de Stock

> Constitución: `docs/constitution.md` principios 1-6 | Spec: `specs/004-consulta-stock/spec.md` RF-1 | Convenciones: `AGENTS.md` | Depende de `001-productos` (stock_inicial, stock_minimo) y `003-movimientos-inventario` (entradas/salidas)

## 1. Estructura de módulos afectados

Respetando arquitectura por capas `routers/ → services/ → models/ + schemas/` y principios 1 y 3 (cálculo de stock solo en `services`).

| Capa | Archivo | Acción | RF cubiertos | Responsabilidad |
|------|---------|--------|--------------|-----------------|
| `models/` | `app/models/producto.py` | **Modificar** | RF-1 | Añadir columna `stock_minimo` (esta spec) — única modificación de modelo |
| `models/` | `app/models/movimiento_inventario.py` | **Reutilizar** | RF-1 | Ya extendido en `003` con `proveedor_id`/`motivo`/`tipo`; solo lectura |
| `schemas/` | `app/schemas/producto.py` | **Modificar** | RF-1 | Extender `ProductoCreate` y `ProductoUpdate` para aceptar `stock_minimo` (validación) y `ProductoResponse`/`ProductoListResponse` para exponerlo |
| `schemas/` | `app/schemas/stock.py` | **Crear** | RF-1 | Pydantic `StockResponse` (`codigo`, `nombre`, `stock_inicial`, `stock_minimo`, `entradas`, `salidas`, `stock_actual`, `alerta`) y `StockListResponse` para listado; validación de `codigo` normalizado |
| `services/` | `app/services/stock_service.py` | **Crear** | RF-1 | Lógica de negocio: cálculo `stock_actual` y `alerta` reutilizando función de `003` |
| `services/` | `app/services/movimiento_service.py` | **Reutilizar/Refactor** | RF-1 | Extraer función de cálculo `calcular_stock` ya existente en `003` a módulo compartido o importarla para evitar duplicación (RNF-2) |
| `routers/` | `app/routers/stock.py` | **Modificar** | RF-1 | Ya creado en `003` para `GET /stock`; ampliar para incluir `stock_minimo`/`alerta` en respuesta y asegurar `GET /stock` y `GET /stock/{codigo}` exponen `alerta` |
| `app/` | `app/main.py` | **Reutilizar** | RF-1 | Ya registra `stock.router`; no cambia prefijo |
| `alembic/` | `alembic/versions/xxxx_stock_minimo_004.py` | **Crear** | RF-1 | Migración que añade `stock_minimo` a `productos` (ver §7) |

> **Aclaración models/**: Solo `productos.stock_minimo` es nuevo. No se crea tabla nueva ni se desnormaliza `stock_actual`. Se consulta lo ya existente (`productos`, `movimientos_inventario`). RF-1.

## 2. Cómo se calcula el stock actual: agregación en consulta vs campo desnormalizado

**Elegida: Cálculo por agregación en el momento de la consulta (RF-1, RNF-2, RNF-3)**

- Implementación: En `stock_service.py`, `calcular_stock_actual(producto_id, stock_inicial, stock_minimo)` ejecuta **una sola consulta agregada** (`SELECT coalesce(SUM(cantidad) FILTER (WHERE tipo='entrada'),0) AS entradas, coalesce(SUM(cantidad) FILTER (WHERE tipo='salida'),0) AS salidas FROM movimientos_inventario WHERE producto_id=:id`) y luego `stock_actual = stock_inicial + entradas - salidas` y `alerta = stock_minimo > 0 and stock_actual < stock_minimo`. Para el listado global (`GET /stock`), se hace **una sola consulta agregada con `GROUP BY producto_id`** para todos los `activos` ordenados por `codigo ASC`, evitando `N+1`.
- Reutilización: La función `calcular_stock` ya implementada en `movimiento_service.py` para `003` se extrae a `stock_service.py` (o se importa) y es usada tanto por `movimiento_service` como por `stock_service` para no duplicar lógica (principio 3, RNF-2).

**Alternativa descartada: Campo desnormalizado `productos.stock_actual` actualizado en cada movimiento (ya resuelto en `003/plan.md:5`)**

- Consistía en añadir columna `stock_actual INTEGER NOT NULL DEFAULT stock_inicial` y hacer `UPDATE productos SET stock_actual = stock_actual + cantidad` dentro de la misma transacción que `INSERT movimientos_inventario`.
- Descartada porque: (a) duplica fuente de verdad (riesgo de divergencia si `stock_actual` y `SUM` no coinciden), (b) requiere `UPDATE` adicional y manejo de concurrencia con `FOR UPDATE` ya necesario de todos modos, (c) para volumen MVP (<10k movimientos/producto) el `SUM` es suficientemente rápido (<50ms) y se beneficia de índices `ix_movimientos_producto_id` y `ix_movimientos_tipo` ya existentes. Se reevaluará con vista materializada si `GET /stock` supera 500ms con 1k productos (RNF-3).

Justificación: **simplicidad y consistencia** (una sola fuente `append-only`) vs **rendimiento** (una columna evita `SUM`); se elige simplicidad porque el cálculo es idempotente y la consulta global ya es agregada única, sin `N+1`.

## 3. Contrato de la API

Base: `/api/v1` (`AGENTS.md`). JSON. Mensajes en español (RNF-4). `codigo` normalizado `trim+mayúsculas` `^[A-Z0-9_-]{3,20}$`.

### RF-1 — Listado global `GET /api/v1/stock`

**Request:**
```
GET /api/v1/stock
```
**Response 200 (con activos, orden `codigo ASC`):**
```json
[
  {
    "codigo": "PROD-001",
    "nombre": "PlayStation 5 Slim",
    "stock_inicial": 5,
    "stock_minimo": 10,
    "entradas": 12,
    "salidas": 3,
    "stock_actual": 14,
    "alerta": false
  },
  {
    "codigo": "PROD-002",
    "nombre": "Zelda TOTK",
    "stock_inicial": 0,
    "stock_minimo": 5,
    "entradas": 0,
    "salidas": 0,
    "stock_actual": 0,
    "alerta": true
  }
]
```
- `alerta: true` si `stock_minimo >0 && stock_actual < stock_minimo` (ej. `0<5` → `true`, `5==5` → `false`).
- Sin `stock_minimo`/`null` → `0` → `false`.

**Response 200 vacío:**
```json
[]
```
Si no hay `activos`.

**Errores:** No hay `404` para listado; siempre `200` con `[]`.

### RF-1 — Detalle por producto `GET /api/v1/stock/{codigo}`

**Request:**
```
GET /api/v1/stock/  prod-001 
```
Normalizado a `PROD-001`.

**Response 200 (activo):**
```json
{
  "codigo": "PROD-001",
  "nombre": "PlayStation 5 Slim",
  "stock_inicial": 5,
  "stock_minimo": 10,
  "entradas": 12,
  "salidas": 3,
  "stock_actual": 14,
  "alerta": false
}
```
**Response 200 sin movimientos:**
```json
{
  "codigo": "PROD-003",
  "nombre": "Mayorista Norte",
  "stock_inicial": 5,
  "stock_minimo": 10,
  "entradas": 0,
  "salidas": 0,
  "stock_actual": 5,
  "alerta": true
}
```
**Errores:**
- `404` si `codigo` no existe → RF-1
- `404` si `codigo` existe pero `estado == inactivo` → RF-1 (solo lectura de `activos`; a diferencia de `001` que devuelve `200` para catálogo, stock no expone `inactivos` para evitar reponerlos)
- `422` si `codigo` viola `^[A-Z0-9_-]{3,20}$` → RF-1 (validación sintáctica en `schemas`)

### Resumen códigos RF-1

| Endpoint | 200 | 404 | 422 |
|----------|-----|-----|-----|
| GET /stock | RF-1 listado |  |  |
| GET /stock/{codigo} | RF-1 detalle | RF-1 no existe/inactivo | RF-1 formato código |

## 4. Reglas de validación: schema vs service

**Principio 3:** `routers/` solo HTTP, `schemas/` sintáctica, `services/` negocio.

**En `schemas/stock.py` y `schemas/producto.py` (Pydantic) — sintáctica, sin I/O, 422 (RF-1):**
- `StockQuery` (para `GET /stock/{codigo}`): `codigo` `trim+mayúsculas` `^[A-Z0-9_-]{3,20}$` (`AGENTS.md` validación vía Pydantic).
- `ProductoCreate`/`ProductoUpdate` extendidos: `stock_minimo` `Optional[int]` `ge=0 le=1_000_000`, `null`/ausente → `0`, `""` → 422, `strict=True` rechaza `1.5`/`"10"`.
- Justificación: declarativas, baratas, 422 inmediato; Pydantic canónico.

**En `services/stock_service.py` — negocio con BD, 404 (RF-1):**
- `codigo` normalizado `trim+upper` ya validado pero se revalida; existencia y `estado == activo` → 404 si no existe o `inactivo` (para stock); no se valida `stock_minimo` aquí (ya validado en `producto_service` al crear/editar).
- Cálculo `stock_actual` y `alerta` (`stock_minimo >0 and stock_actual < stock_minimo`) se hace en `services`, no en `routers` ni en `schemas`, para reutilizar lógica de `003` y respetar principio 3.
- Justificación: requiere estado persistido (`productos.stock_minimo`, `movimientos`); no pertenece a `schema` (principio 5 no aplica `DELETE`, pero RNF-1 solo lectura).

## 5. Decisiones técnicas relevantes

1. **`stock_minimo` como columna en `productos` vs tabla separada `stock_minimos`**
   - Elegida: `productos.stock_minimo INTEGER NOT NULL DEFAULT 0`.
   - Descartada: tabla `stock_minimos(producto_id, minimo)` con `FK`.
   - Motivo: `stock_minimo` es atributo 1:1 del producto, cardinalidad fija, no requiere historial; columna simplifica `JOIN` y `GROUP BY` para listado global. RF-1, RNF-5.

2. **Listado `GET /stock` sin paginación vs con `?limit&offset`**
   - Elegida: sin paginación, devuelve todo ordenado `codigo ASC` (RNF-3, `spec.md:46` fuera de alcance).
   - Descartada: paginación obligatoria `?page&size`.
   - Motivo: volumen MVP <1k productos activos, <500ms con índice `ix_productos_codigo` y agregación única; se añadirá sin breaking change como `?limit&offset` opcional. RF-1.

3. **Ordenamiento `codigo ASC` vs `stock_actual ASC` o `alerta DESC`**
   - Elegida: `codigo ASC` determinista.
   - Descartada: ordenar por `alerta` primero o por `stock_actual` ascendente.
   - Motivo: `codigo` es PK de negocio estable y predecible para tests; ordenar por `alerta` ocultaría productos sin alerta y rompería comparabilidad con `001` listado. Se puede añadir `?sort=alerta` futuro. RF-1.

4. **Filtro `?alerta=true` vs sin filtro**
   - Elegida: sin filtro en MVP (siempre lista completa con `alerta`).
   - Descartada: `GET /stock?alerta=true` que devuelve solo en alerta.
   - Motivo: `spec.md:46` fuera de alcance `alerta=true` obligatorio; cliente puede filtrar en memoria con `alerta`; se añadirá como filtro opcional sin breaking. RF-1.

5. **`GET /stock/{codigo}` con `inactivo` → 404 vs 200 con `alerta`**
   - Elegida: `404` si `inactivo` (RF-1).
   - Descartada: `200` con `alerta` para `inactivo`.
   - Motivo: stock de `inactivo` no es accionable (no se debe reponer), y `001` ya expone `inactivo` en catálogo para trazabilidad; stock solo para `activos` evita confusión y mantiene `RNF-1` solo lectura de activos. RF-1.

6. **Reutilizar cálculo de `movimiento_service` vs duplicar en `stock_service`**
   - Elegida: extraer función `calcular_stock(db, producto_id, stock_inicial, stock_minimo)` compartida e importada por ambos services.
   - Descartada: copiar `SUM` en `stock_service`.
   - Motivo: principio 3 y RNF-2 (misma fórmula `inicial + entradas - salidas` sin `entrada_inicial`); evita divergencia. RF-1, RNF-2.

7. **`stock_actual` calculado en cada request vs cache en Redis**
   - Elegida: calcular en cada request con `SUM` + `GROUP BY`.
   - Descartada: cache `stock_actual` en `productos` o Redis con TTL.
   - Motivo: consistencia inmediata tras `POST /movimientos` es crítica para decidir reposición; cache añadiría invalidez y complejidad; se evaluará si `GET /stock` supera 500ms. RF-1, RNF-3.

## 6. Plan de migración Alembic si corresponde

**Sí corresponde (RF-1):** `stock_minimo` es columna nueva en `productos`, no solo consulta. Además, se añade índice para optimizar `alerta` si se filtra en el futuro, pero no es obligatorio para MVP.

**Revisión:** `alembic revision --autogenerate -m "agrega stock_minimo a productos"` → `alembic upgrade head` sin errores (principio 5).

**Cambios:**
- `productos` añadir `stock_minimo INTEGER NOT NULL DEFAULT 0 CHECK (stock_minimo >=0 AND stock_minimo <=1000000)` (ver §5.1).
- Índice opcional para alerta: `ix_productos_stock_minimo` no necesario para MVP porque `alerta` se calcula en Python tras `SUM`, pero se puede añadir `CREATE INDEX ix_productos_estado_codigo ON productos (estado, codigo)` ya existente para `WHERE estado='activo' ORDER BY codigo`.
- No toca `movimientos_inventario` (ya en `9111dba96a53`), no toca `proveedores`.
- **Extensión de `ProductoUpdate`:** `PATCH /api/v1/productos/{sku}` ya existe en `001` y se modifica para aceptar `stock_minimo` opcional (`null` → `0`, `""`→422) sin nueva migración de endpoint, solo de columna.
- Verificación: `alembic upgrade head` y `downgrade -1` + `upgrade` sin pérdida; `psql \d productos` muestra `stock_minimo integer NOT NULL DEFAULT 0`.

**Alternativa descartada:** No hacer migración y calcular `stock_minimo` como `0` hardcodeado en `stock_service` — violaría `RNF-5` (persistencia de mínimo) y no permitiría alertas reales.

## 7. Estrategia de tests

Sin escribir código de tests (principio 4: `pytest -v` verde).

**Unitarios — `services/stock_service.py` (mock `Session` / `sqlite:///:memory:` con `Base.metadata.create_all`):**
- RF-1: stock sin movimientos `stock_actual==stock_inicial` y `alerta` según `minimo` (`0`→`false`, `5` con `inicial 5`→`false`, `10` con `inicial 5`→`true`); `stock_minimo` `null`→`0`; `stock_inicial 5` + `entrada 10` - `salida 3` = `12` con `minimo 10`→`false`, luego `salida 5` deja `7`→`true`; `codigo` `3`/`20` con `trim+upper`, `AB`/`A*21`→`422`; `inactivo`→`404`.
- RF-1 `alerta` estricta: `stock_actual == stock_minimo` (5/5) → `false`, `stock_actual 0` con `minimo 5` → `true`, `stock_actual 2_000_000` con `minimo 1_000_000` → `false` (límite por movimiento, no por acumulado).
- RF-1 `stock_minimo` validación: `POST /productos` con `stock_minimo` `1`, `1000000`, `0`, `null`/ausente → `0`; `"-5"`, `""`, `1.5`, `>1M` → `422` (vía `ProductoCreate` extendido).

**Integración — `routers/stock.py` + `routers/productos.py` (`TestClient` + `TestSession` con `productos`/`proveedores`/`movimientos` creados via `POST` previos):**
- RF-1: `GET /api/v1/stock` `200` `[]` vacío, `200` lista de `activos` ordenada `codigo ASC` con `stock_minimo` y `alerta` (`inactivo` excluido), `GET /stock/PROD-001` `200` con `alerta` `false`→`true` tras `salida`, `404` inexistente/`inactivo`/`AB`, normalizado `  prod-001 `; `POST /productos` con `stock_minimo` `10` y `GET /stock` refleja `alerta`; `PATCH /productos/{sku}` con `stock_minimo` `0`→`false` y `null`→`0`.
- Transversal: mensajes en español, sin exponer modelos SQLAlchemy, `stock_actual` nunca negativo (heredado de `003`), `ruff`/`mypy` pasan, `GET /docs` lista `GET /stock` y `GET /stock/{codigo}` (2 endpoints nuevos, total 16).

Cada test mapea a su RF y RNF-1..RNF-5.
