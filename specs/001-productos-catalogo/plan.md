# Plan 001 — Catálogo de Productos

> Constitución: `docs/constitution.md` principios 1-6 | Spec: `specs/001-productos-catalogo/spec.md` RF-1..RF-5 | Convenciones: `AGENTS.md`

## 1. Estructura de módulos afectados

Respetando arquitectura por capas `routers/ → services/ → models/ + schemas/` y principio 3 (lógica separada de interfaz).

| Capa | Archivo | Acción | RF cubiertos | Responsabilidad |
|------|---------|--------|--------------|-----------------|
| `models/` | `app/models/producto.py` | **Crear** | RF-1, RF-4, RF-5 | Entidad `Producto` (singular) tabla `productos` |
| `models/` | `app/models/movimiento_inventario.py` | **Crear** | RF-1 | Entidad `MovimientoInventario` tabla `movimientos_inventario` solo para traza inicial (append-only, principio 5) |
| `schemas/` | `app/schemas/producto.py` | **Crear** | RF-1..RF-5 | Pydantic para validación I/O; nunca exponer modelos SQLAlchemy (AGENTS.md) |
| `services/` | `app/services/producto_service.py` | **Crear** | RF-1..RF-5 | Lógica de negocio: normalización, unicidad, estado, traza inicial |
| `routers/` | `app/routers/productos.py` | **Crear** | RF-1..RF-5 | Endpoints REST bajo `/api/v1/productos`; solo HTTP + delegación a service |
| `app/` | `app/main.py` | **Modificar** | RF-1..RF-5 | Registrar `productos.router` con prefijo `/api/v1` |
| `alembic/` | `alembic/versions/xxxx_crea_catalogo_productos.py` | **Crear** | RF-1, RF-5 | Migración inicial del esquema (ver §6) |

> Verificación principio 1: `ruff check .`, `mypy app` y estructura de carpetas.

## 2. Modelo de datos

### 2.1 Tabla `productos`
Modelo `Producto` → tabla `productos` (plural).

| Columna | Tipo SQLAlchemy/PostgreSQL | Restricciones | Índice |
|---------|----------------------------|---------------|--------|
| `id` | `Integer` PK autoincrement | PK | PK |
| `sku` | `VARCHAR(20)` | `NOT NULL`, `UNIQUE`, almacena valor **normalizado** (`trim`+`mayúsculas`), check `~ '^[A-Z0-9_-]{3,20}$'` | `UNIQUE INDEX ix_productos_sku` |
| `nombre` | `VARCHAR(100)` | `NOT NULL`, check `length(trim(nombre)) BETWEEN 2 AND 100` | — |
| `categoria` | `VARCHAR(20)` | `NOT NULL`, check `categoria IN ('videojuego','consola','accesorio')` | `INDEX ix_productos_categoria` |
| `stock_inicial` | `Integer` | `NOT NULL DEFAULT 0`, check `>=0 AND <=1000000` | — |
| `estado` | `VARCHAR(10)` | `NOT NULL DEFAULT 'activo'`, check `IN ('activo','inactivo')` | `INDEX ix_productos_estado` |
| `created_at` | `DateTime(timezone=True)` | `NOT NULL DEFAULT now()` | — |
| `updated_at` | `DateTime(timezone=True)` | `NOT NULL DEFAULT now() ON UPDATE now()` | — |

RF: RF-1 (alta con validaciones), RF-4 (edición nombre/categoria), RF-5 (cambio estado), RF-2/RF-3 (consulta).

### 2.2 Tabla `movimientos_inventario`
Modelo `MovimientoInventario` → tabla `movimientos_inventario` (solo traza inicial de este spec; resto de movimientos en spec futura).

| Columna | Tipo | Restricciones | Índice/FK |
|---------|------|---------------|-----------|
| `id` | `Integer` PK | PK | PK |
| `producto_id` | `Integer` | `NOT NULL`, FK `productos.id` `ON DELETE RESTRICT` | `FK + INDEX ix_movimientos_producto_id` |
| `tipo` | `VARCHAR(10)` | `NOT NULL`, check `IN ('entrada_inicial')` | — |
| `cantidad` | `Integer` | `NOT NULL`, check `>0 AND <=1000000` | — |
| `created_at` | `DateTime(timezone=True)` | `NOT NULL DEFAULT now()` | — |

Principio 5: tabla append-only — sin `UPDATE`/`DELETE` permitidos a nivel de service; histórico inmutable.

### 2.3 Ejemplo de fila representativa

`productos`:
```json
{
  "id": 1,
  "sku": "PS5-SLIM-001",
  "nombre": "PlayStation 5 Slim",
  "categoria": "consola",
  "stock_inicial": 10,
  "estado": "activo",
  "created_at": "2026-09-07T10:00:00Z",
  "updated_at": "2026-09-07T10:00:00Z"
}
```
`movimientos_inventario` (generado solo si `stock_inicial >0` — RF-1):
```json
{
  "id": 1,
  "producto_id": 1,
  "tipo": "entrada_inicial",
  "cantidad": 10,
  "created_at": "2026-09-07T10:00:00Z"
}
```
Con `stock_inicial=0` no se crea fila en `movimientos_inventario`.

## 3. Contrato de la API

Base: `/api/v1` (AGENTS.md). Todos los JSON con `Content-Type: application/json`. Mensajes de error en español (RNF-2).

### RF-1 — Alta `POST /api/v1/productos`

**Request 201 (éxito):**
```json
POST /api/v1/productos
{
  "sku": "  ps5-slim-001 ",
  "nombre": "PlayStation 5 Slim",
  "categoria": "consola",
  "stock_inicial": 10
}
```
Normalización: `sku` → `PS5-SLIM-001`, `categoria` → `consola`.

**Response 201:**
```json
{
  "sku": "PS5-SLIM-001",
  "nombre": "PlayStation 5 Slim",
  "categoria": "consola",
  "stock_inicial": 10,
  "estado": "activo"
}
```
**Response 201 con `stock_inicial` omitido/null:**
```json
{
  "sku": "XBOX-SERIES-X",
  "nombre": "Xbox Series X",
  "categoria": "consola",
  "stock_inicial": 0,
  "estado": "activo"
}
```
**Errores:**
- `400` validación Pydantic (longitud/formato/enum/rango) → RF-1
- `409` SKU duplicado (incluye inactivo, tras normalización) → RF-1
- `422` `stock_inicial` negativo/decimal/no numérico/>1M → RF-1

Cubre RF-1 completo.

### RF-2 — Listado activos `GET /api/v1/productos`

**Request:**
```
GET /api/v1/productos
```
**Response 200 (con activos):**
```json
[
  {"sku":"PS5-SLIM-001","nombre":"PlayStation 5 Slim","categoria":"consola","stock_inicial":10},
  {"sku":"ZELDA-TOTK-NS","nombre":"Zelda TOTK","categoria":"videojuego","stock_inicial":0}
]
```
**Response 200 (vacío):**
```json
[]
```
Inactivos excluidos. Cubre RF-2.

### RF-3 — Detalle por SKU `GET /api/v1/productos/{sku}`

**Request:**
```
GET /api/v1/productos/ ps5-slim-001
```
Normalizado a `PS5-SLIM-001`.

**Response 200 (activo):**
```json
{
  "sku": "PS5-SLIM-001",
  "nombre": "PlayStation 5 Slim",
  "categoria": "consola",
  "stock_inicial": 10,
  "estado": "activo"
}
```
**Response 200 (inactivo — trazabilidad):**
```json
{
  "sku": "PS5-SLIM-001",
  "nombre": "PlayStation 5 Slim",
  "categoria": "consola",
  "stock_inicial": 10,
  "estado": "inactivo"
}
```
**Error `404` SKU no encontrado** → RF-3.

Cubre RF-3.

### RF-4 — Edición `PATCH /api/v1/productos/{sku}`

**Request (parcial):**
```json
PATCH /api/v1/productos/PS5-SLIM-001
{
  "nombre": "PlayStation 5 Slim Edición Digital",
  "categoria": "consola"
}
```
**Response 200:**
```json
{
  "sku": "PS5-SLIM-001",
  "nombre": "PlayStation 5 Slim Edición Digital",
  "categoria": "consola",
  "stock_inicial": 10,
  "estado": "activo"
}
```
**Errores:**
- `404` no encontrado → RF-4
- `400` inactivo no editable → RF-4
- `400` `nombre` vacío / longitud inválida / `categoria` inválida → RF-4
- `400` payload incluye `sku` distinto al path → RF-4 (mismo valor se ignora)
- `400` intento de editar `stock_inicial`/`estado` → ignorado/rechazado → RF-4

Cubre RF-4.

### RF-5 — Baja lógica `DELETE /api/v1/productos/{sku}`

**Request:**
```
DELETE /api/v1/productos/PS5-SLIM-001
```
**Response 200:**
```json
{
  "sku": "PS5-SLIM-001",
  "nombre": "PlayStation 5 Slim",
  "categoria": "consola",
  "stock_inicial": 10,
  "estado": "inactivo"
}
```
**Errores:**
- `404` no encontrado → RF-5
- `400` ya inactivo → RF-5

Sin validar stock (RF-5). Cubre RF-5.

### Tabla resumen códigos

| Endpoint | 200 | 201 | 400 | 404 | 409 |
|----------|-----|-----|-----|-----|-----|
| POST /productos |  | RF-1 éxito | RF-1 validación |  | RF-1 duplicado |
| GET /productos | RF-2 |  |  |  |  |
| GET /productos/{sku} | RF-3 |  |  | RF-3 |  |
| PATCH /productos/{sku} | RF-4 |  | RF-4 inactivo/inmutable/validación | RF-4 |  |
| DELETE /productos/{sku} | RF-5 |  | RF-5 ya inactivo | RF-5 |  |

## 4. Reglas de validación: schema vs service

**Principio 3:** `routers/` solo HTTP, `schemas/` validación sintáctica, `services/` lógica de negocio. `schemas/` nunca toca BD; `services/` nunca expone SQLAlchemy.

**En `schemas/producto.py` (Pydantic) — validación sintáctica/de formato, falla con 400/422 antes de tocar BD:**
- RF-1/RF-4: `nombre` `2-100` tras `strip`, no vacío; `sku` `3-20` regex `^[A-Za-z0-9_-]+$` (normalización posterior en service), requerido; `categoria` enum `videojuego|consola|accesorio` tras `strip+lower`; `stock_inicial` opcional `int >=0 <=1_000_000`, rechazo de decimal/string; `sku` inmutable no validado aquí (se valida en service).
- RF-4 `ProductoUpdate`: `nombre`/`categoria` opcionales pero al menos uno presente, mismas reglas de longitud/enum; rechaza payload vacío.
- Justificación: son reglas declarativas, sin I/O, baratas y dan feedback inmediato 400; Pydantic es el lugar canónico (AGENTS.md).

**En `services/producto_service.py` — lógica de negocio con acceso a BD, falla con 404/409/400 de negocio:**
- RF-1: normalización `sku` `trim+upper` y `categoria` `trim+lower`; unicidad global de `sku` incluyendo inactivos (consulta + `UNIQUE` DB como salvaguarda); creación de traza `entrada_inicial` si `stock_inicial>0` en la misma transacción; manejo de carrera por `IntegrityError` → 409.
- RF-3/RF-4/RF-5: existencia por `sku` normalizado → 404; verificación `estado=='inactivo'` → 400 no editable/ya dado de baja (RF-4/RF-5).
- RF-4: inmutabilidad de `sku` (si `payload.sku` normalizado != `path_sku` → 400), ignorar `stock_inicial`/`estado` si vienen en payload.
- RF-2/RF-3: filtrado por `estado` y aplicación de normalización en lectura.
- Justificación: requieren estado persistido y transacción; no pertenecen al schema porque dependen de BD y de reglas de dominio (principio 5 append-only, RNF-3).

## 5. Decisiones técnicas

1. **Baja lógica (`estado` inactivo) vs borrado físico DELETE**
   - Elegida: `estado` con `DELETE` lógico (endpoint `DELETE` cambia a `inactivo`).
   - Descartada: `DELETE FROM productos` físico.
   - Motivo: cumple RNF-1 y principio 5 (preservar historial), permite detalle de inactivos (RF-3) y evita violar FK de `movimientos`. Físico perdería trazabilidad.

2. **SKU normalizado en columna única vs dos columnas (original + normalizada) vs normalización solo en app**
   - Elegida: almacenar `sku` ya normalizado con `UNIQUE` y `CHECK` regex, normalizar en service (`trim+upper`) antes de persistir/consultar.
   - Descartada: dos columnas o solo validación en app sin constraint DB.
   - Motivo: garantiza unicidad case-insensitive a nivel DB (carrera), simplifica modelo y cumple RNF-3; segunda columna añade complejidad innecesaria para MVP.

3. **Manejo de SKU duplicado: `UNIQUE` DB + captura `IntegrityError` vs solo check `SELECT` previo**
   - Elegida: ambas — check previo para mensaje 409 amigable + `UNIQUE` como barrera de carrera.
   - Descartada: solo `SELECT` previo.
   - Motivo: evita condición de carrera concurrente (caso límite spec).

4. **Traza inicial en `movimientos_inventario` dentro de la misma transacción vs sin traza**
   - Elegida: crear fila `entrada_inicial` si `stock_inicial>0` en transacción atómica con `productos`.
   - Descartada: solo guardar `stock_inicial` sin traza o traza asíncrona.
   - Motivo: satisface RF-1 y RNF-5 manteniendo append-only y atomicidad; sin traza se perdería auditoría y violaría principio 5.

5. **`PATCH /productos/{sku}` vs `PUT` para edición**
   - Elegida: `PATCH` parcial (al menos un campo `nombre`/`categoria`).
   - Descartada: `PUT` total que obligue a enviar todo el recurso.
   - Motivo: RF-4 permite editar `nombre` y/o `categoria`; `PATCH` es más flexible y evita sobreescritura accidental de campos no editables; ambos son REST válidos (AGENTS.md).

6. **`categoria` como `VARCHAR + CHECK` vs `PostgreSQL ENUM`**
   - Elegida: `VARCHAR(20)` con `CHECK IN (...)`.
   - Descartada: `ENUM` nativo.
   - Motivo: más fácil de migrar con Alembic y de evolucionar sin `ALTER TYPE`; cumple validación sin acoplar DB a dominio cerrado del MVP.

7. **`stock_inicial` en `productos` vs cálculo derivado de `movimientos`**
   - Elegida: columna `stock_inicial` en `productos` + traza espejo en `movimientos` solo para este spec.
   - Descartada: solo movimientos y `stock_inicial` derivado.
   - Motivo: spec declara que cálculo de stock actual es de spec futura; guardar `stock_inicial` evita acoplar catálogo a lógica de inventario completa en este MVP, manteniendo RNF-5.

## 6. Plan de migración Alembic

**Revisión:** `alembic revision --autogenerate -m "crea catalogo productos"` → `alembic upgrade head` debe pasar sin errores (AGENTS.md/constitución principio 5).

**Cambios:**
- Crear tabla `productos` con columnas, checks e índices descritos en §2.1.
- Crear tabla `movimientos_inventario` con FK a `productos.id` y checks de §2.2.
- Índices: `ix_productos_sku` UNIQUE, `ix_productos_categoria`, `ix_productos_estado`, `ix_movimientos_producto_id`.
- No se modifica esquema existente (migración inicial); si `productos` ya existe, la migración añade `estado` y `stock_inicial` con defaults y backfill (`estado='activo'`).

**Verificación:** `alembic upgrade head` y `alembic downgrade -1` + `upgrade` sin pérdida de datos; `psql \d productos` muestra constraints.

## 7. Estrategia de tests

Sin escribir código de tests (principio 4: `pytest -v` 100% verde al finalizar).

**Unitarios — `services/producto_service.py` (mock de DB/session):**
- RF-1: alta válida con `stock_inicial` 0/10/null → crea y genera/no genera traza; duplicado normalizado (`ps5-001` vs ` PS5-001 `) → 409; nombre vacío/largo, sku corto/largo/caracteres inválidos, categoria `juego`/`VIDEOJUEGO` → 400; stock negativo/decimal/>1M → 400; duplicado tras inactivo → 409.
- RF-4: edición válida parcial/total → actualiza; sku distinto en payload → 400; sku igual → ignora; inactivo → 400; no encontrado → 404; validación nombre/categoria → 400; intento editar `stock_inicial`/`estado` → ignorado.
- RF-5: baja activo → `inactivo`; ya inactivo → 400; no encontrado → 404; con `stock_inicial>0` permite → 200.
- RF-2/RF-3: normalización en consulta; carrera por `IntegrityError` simulada → 409.

**Integración — `routers/productos.py` (TestClient + DB de test PostgreSQL):**
- RF-1: `POST /api/v1/productos` 201 + traza en `movimientos_inventario` verificada; 409 duplicado; 400 validación Pydantic.
- RF-2: `GET /api/v1/productos` devuelve solo activos; vacío → `[]`; inactivo excluido.
- RF-3: `GET /api/v1/productos/{sku}` con SKU normalizado/variado case/espacios → 200 activo/inactivo; 404 inexistente.
- RF-4: `PATCH /api/v1/productos/{sku}` 200; 400 inmutable/inactivo/validación; 404 no encontrado; verifica que `sku` no cambia y que campos extra se ignoran.
- RF-5: `DELETE /api/v1/productos/{sku}` 200 y posterior `GET` detalle muestra `inactivo`; `GET` listado ya no lo incluye; 400 ya inactivo; 404 no encontrado.
- Transversal: mensajes en español, sin exponer modelos SQLAlchemy (respuesta solo schemas), `ruff`/`mypy` pasan.

Cada test mapea explícitamente a su RF y a RNF-1..RNF-5.
