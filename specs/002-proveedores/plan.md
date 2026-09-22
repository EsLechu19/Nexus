# Plan 002 — Gestión de Proveedores

> Constitución: `docs/constitution.md` principios 1-6 | Spec: `specs/002-proveedores/spec.md` RF-1..RF-5 | Convenciones: `AGENTS.md`

## 1. Estructura de módulos afectados

Respetando arquitectura por capas `routers/ → services/ → models/ + schemas/` y principios 1 y 3.

| Capa | Archivo | Acción | RF cubiertos | Responsabilidad |
|------|---------|--------|--------------|-----------------|
| `models/` | `app/models/proveedor.py` | **Crear** | RF-1, RF-4, RF-5 | Entidad `Proveedor` (singular) tabla `proveedores` |
| `schemas/` | `app/schemas/proveedor.py` | **Crear** | RF-1..RF-5 | Pydantic para validación I/O; nunca expone modelos SQLAlchemy |
| `services/` | `app/services/proveedor_service.py` | **Crear** | RF-1..RF-5 | Lógica de negocio: normalización, unicidad, estado, edición/baja |
| `routers/` | `app/routers/proveedores.py` | **Crear** | RF-1..RF-5 | Endpoints REST bajo `/api/v1/proveedores`; solo HTTP + delegación |
| `app/` | `app/main.py` | **Modificar** | RF-1..RF-5 | Registrar `proveedores.router` (ya existe `productos.router`) |
| `alembic/` | `alembic/versions/xxxx_crea_proveedores.py` | **Crear** | RF-1, RF-5 | Migración que crea `proveedores` (ver §7) |

> RF-1 alta, RF-2 listado, RF-3 detalle, RF-4 edición, RF-5 baja — todos mapeados a capas. Verificación principio 1: `ruff check .`, `mypy app`.

## 2. Modelo de datos

### 2.1 Tabla `proveedores`
Modelo `Proveedor` → tabla `proveedores` (plural, `AGENTS.md`). Sin FK saliente; será referenciada por `003-movimientos-inventario`.

| Columna | Tipo SQLAlchemy/PostgreSQL | Restricciones | Índice |
|---------|----------------------------|---------------|--------|
| `id` | `Integer` PK autoincrement | PK | PK |
| `codigo` | `VARCHAR(20)` | `NOT NULL`, `UNIQUE`, almacena **normalizado** (`trim`+`mayúsculas`), check `length(codigo) BETWEEN 3 AND 20` + regex `^[A-Z0-9_-]{3,20}$` (comentario para SQLite) | `UNIQUE INDEX ix_proveedores_codigo` |
| `nombre` | `VARCHAR(100)` | `NOT NULL`, check `length(trim(nombre)) BETWEEN 2 AND 100` | `INDEX ix_proveedores_nombre` (opcional, para listado ordenado) |
| `email` | `VARCHAR(254)` | `NULL`, check `email ~ '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'` o `NULL` | — |
| `telefono` | `VARCHAR(20)` | `NULL`, check `telefono ~ '^\+?[0-9 ()-]{7,20}$'` + dígitos 7-15 (validado en app, check laxo en DB) | — |
| `direccion` | `VARCHAR(200)` | `NULL`, check `length(trim(direccion)) BETWEEN 5 AND 200` o `NULL` | — |
| `estado` | `VARCHAR(10)` | `NOT NULL DEFAULT 'activo'`, check `IN ('activo','inactivo')` | `INDEX ix_proveedores_estado` |
| `created_at` | `DateTime(timezone=True)` | `NOT NULL DEFAULT now()` | — |
| `updated_at` | `DateTime(timezone=True)` | `NOT NULL DEFAULT now() ON UPDATE now()` | — |

RF: RF-1 (alta con validaciones y unicidad), RF-4 (edición nombre/contacto), RF-5 (cambio estado), RF-2/RF-3 (consulta). RNF-1 y RNF-3 garantizados por `UNIQUE` + `estado`.

### 2.2 Ejemplo de fila representativa

`proveedores`:
```json
{
  "id": 1,
  "codigo": "PROV-001",
  "nombre": "Distribuidora Central",
  "email": "contacto@central.com",
  "telefono": "+34 912 345 678",
  "direccion": "Calle Mayor 10, Madrid",
  "estado": "activo",
  "created_at": "2026-09-08T10:00:00Z",
  "updated_at": "2026-09-08T10:00:00Z"
}
```
Con contacto mínimo:
```json
{
  "id": 2,
  "codigo": "PROV-002",
  "nombre": "Mayorista Norte",
  "email": null,
  "telefono": null,
  "direccion": null,
  "estado": "activo",
  "created_at": "2026-09-08T10:00:00Z",
  "updated_at": "2026-09-08T10:00:00Z"
}
```

### 2.3 Referencia futura para 003
Para `003-movimientos-inventario` se expondrá `proveedores.id` como `Integer` PK. La columna FK en `movimientos_inventario` será `proveedor_id INTEGER NOT NULL REFERENCES proveedores(id) ON DELETE RESTRICT` (ver §6 Nota). `003` validará en service que el `proveedor_id` exista y que `proveedores.estado == 'activo'` antes de crear entrada; si es `inactivo` rechazará 400. Esto resuelve `spec.md:4` y `RNF-5`.

## 3. Contrato de la API

Base: `/api/v1` (`AGENTS.md`). JSON `Content-Type: application/json`. Mensajes en español (RNF-2). Todos los `codigo` se normalizan en entrada/salida a `trim+mayúsculas`.

### RF-1 — Alta `POST /api/v1/proveedores`

**Request 201:**
```json
POST /api/v1/proveedores
{
  "codigo": "  prov-001 ",
  "nombre": "Distribuidora Central",
  "email": "  CONTACTO@central.com ",
  "telefono": "+34 912 345 678",
  "direccion": "Calle Mayor 10"
}
```
Normalización: `codigo` → `PROV-001`, `email` → `contacto@central.com`.

**Response 201:**
```json
{
  "codigo": "PROV-001",
  "nombre": "Distribuidora Central",
  "email": "contacto@central.com",
  "telefono": "+34 912 345 678",
  "direccion": "Calle Mayor 10",
  "estado": "activo"
}
```
**Response 201 sin contacto:**
```json
{
  "codigo": "PROV-002",
  "nombre": "Mayorista Norte",
  "email": null,
  "telefono": null,
  "direccion": null,
  "estado": "activo"
}
```
**Errores:**
- `422` validación Pydantic (código 3-20 regex, nombre 2-100, email/telefono/direccion formato) → RF-1
- `409` código duplicado (incluye inactivo, tras normalización) → RF-1

### RF-2 — Listado activos `GET /api/v1/proveedores`

**Request:**
```
GET /api/v1/proveedores
```
**Response 200 (con activos):**
```json
[
  {"codigo":"PROV-001","nombre":"Distribuidora Central","email":"contacto@central.com","telefono":"+34 912 345 678","direccion":"Calle Mayor 10"},
  {"codigo":"PROV-002","nombre":"Mayorista Norte","email":null,"telefono":null,"direccion":null}
]
```
Sin campo `estado` (implícitamente `activo`). Ordenado por `codigo`.

**Response 200 vacío:**
```json
[]
```
Inactivos excluidos. Cubre RF-2.

### RF-3 — Detalle por código `GET /api/v1/proveedores/{codigo}`

**Request:**
```
GET /api/v1/proveedores/ prov-001
```
Normalizado a `PROV-001`.

**Response 200 activo:**
```json
{
  "codigo": "PROV-001",
  "nombre": "Distribuidora Central",
  "email": "contacto@central.com",
  "telefono": "+34 912 345 678",
  "direccion": "Calle Mayor 10",
  "estado": "activo"
}
```
**Response 200 inactivo (trazabilidad):**
```json
{
  "codigo": "PROV-001",
  "nombre": "Distribuidora Central",
  "email": "contacto@central.com",
  "telefono": "+34 912 345 678",
  "direccion": "Calle Mayor 10",
  "estado": "inactivo"
}
```
**Error `404` código no encontrado** → RF-3.

### RF-4 — Edición `PATCH /api/v1/proveedores/{codigo}`

**Request:**
```json
PATCH /api/v1/proveedores/PROV-001
{
  "nombre": "Distribuidora Central SL",
  "email": null,
  "telefono": "+34 600 123 456"
}
```
`null` borra campo, ausente deja sin cambios, `""` → 422.

**Response 200:**
```json
{
  "codigo": "PROV-001",
  "nombre": "Distribuidora Central SL",
  "email": null,
  "telefono": "+34 600 123 456",
  "direccion": "Calle Mayor 10",
  "estado": "activo"
}
```
**Errores:**
- `404` no encontrado → RF-4
- `400` inactivo no editable → RF-4
- `400` `codigo` distinto inmutable → RF-4 (mismo valor se ignora, `estado` se ignora)
- `422` `nombre`/`email`/`telefono`/`direccion` inválidos o payload vacío → RF-4

### RF-5 — Baja lógica `DELETE /api/v1/proveedores/{codigo}`

**Request:**
```
DELETE /api/v1/proveedores/PROV-001
```
**Response 200:**
```json
{
  "codigo": "PROV-001",
  "nombre": "Distribuidora Central",
  "email": "contacto@central.com",
  "telefono": "+34 912 345 678",
  "direccion": "Calle Mayor 10",
  "estado": "inactivo"
}
```
**Errores:**
- `404` no encontrado → RF-5
- `400` ya inactivo → RF-5

Permite baja con movimientos previos (no valida `movimientos_inventario`). Cubre RF-5 y RNF-5 (tras baja, `003` rechazará nuevas entradas).

### Resumen códigos

| Endpoint | 200 | 201 | 400 | 404 | 409 | 422 |
|----------|-----|-----|-----|-----|-----|-----|
| POST /proveedores |  | RF-1 |  |  | RF-1 duplicado | RF-1 validación |
| GET /proveedores | RF-2 |  |  |  |  |  |
| GET /proveedores/{codigo} | RF-3 |  |  | RF-3 |  |  |
| PATCH /proveedores/{codigo} | RF-4 |  | RF-4 inmutable/inactivo | RF-4 |  | RF-4 validación/vacío |
| DELETE /proveedores/{codigo} | RF-5 |  | RF-5 ya inactivo | RF-5 |  |  |

## 4. Reglas de validación: schema vs service

**Principio 3:** `routers/` solo HTTP, `schemas/` validación sintáctica, `services/` lógica de negocio.

**En `schemas/proveedor.py` (Pydantic) — sintáctica, sin I/O, 400/422 antes de BD (RF-1, RF-4):**
- RF-1/RF-4: `codigo` `trim+mayúsculas` `^[A-Z0-9_-]{3,20}$`; `nombre` `trim` 2-100; `email` `trim+minúsculas` regex `^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$` y `<=254`; `telefono` `trim` con dígitos 7-15, permite `+` solo inicio + ` ` `-` `()`; `direccion` `trim` 5-200; `codigo`/`nombre` requeridos, `email`/`telefono`/`direccion` `Optional` con `null` permitido y `""` → 422; `ProveedorUpdate` exige ≥1 de `nombre/email/telefono/direccion` ( `codigo`/`estado` no cuentan).
- Justificación: declarativas, baratas, feedback inmediato; Pydantic es canónico (`AGENTS.md`).

**En `services/proveedor_service.py` — negocio con BD, 404/409/400 (RF-1..RF-5):**
- RF-1: normalización `codigo` `trim+upper` y `email` `trim+lower`; unicidad global incluyendo inactivos (`SELECT` + `UNIQUE` DB, `IntegrityError` → 409 RNF-3); `telefono` se almacena conservando formato original pero se valida por conteo de dígitos.
- RF-4: `codigo` inmutable (`payload.codigo` normalizado `!=` path → 400, igual → ignorar, `estado` siempre ignorar); `null` borra contacto vs ausente no cambia; `""` ya rechazado en schema; verificación `estado == 'inactivo'` → 400.
- RF-2/RF-3/RF-5: existencia por `codigo` normalizado → 404; `estado` `inactivo` → 400 no editable / ya dado de baja; filtrado `estado == 'activo'` para listado; manejo `IntegrityError` carrera → 409.
- Justificación: requieren estado persistido y transacción; no pertenecen a schema (principio 5, RNF-3/5).

## 5. Decisiones técnicas

1. **Baja lógica (`estado` inactivo) vs borrado físico `DELETE`**
   - Elegida: `estado` `inactivo` via `DELETE` lógico.
   - Descartada: `DELETE FROM proveedores`.
   - Motivo: RNF-1 y principio 5 (trazabilidad), permite detalle de inactivos (RF-3) y no rompe FK de futuros `movimientos_inventario`. Físico perdería historial y violaría prerrequisito 003. RF-5.

2. **Código normalizado en columna única vs dos columnas (original + normalizada)**
   - Elegida: almacenar `codigo` ya normalizado con `UNIQUE` y `CHECK` regex.
   - Descartada: dos columnas o solo validación en app.
   - Motivo: garantiza unicidad case-insensitive en DB (carrera) y cumple RNF-3 con simplicidad; segunda columna innecesaria para MVP. RF-1.

3. **`email`/`telefono` opcionales con `null` vs `NOT NULL` con default `""`**
   - Elegida: `NULL` en DB, `Optional` en Pydantic, `""` → 422, `null`/ausente → `NULL`.
   - Descartada: `NOT NULL DEFAULT ''` y `""` como vacío.
   - Motivo: distingue “no informado” vs “borrado” (RF-4 `null` borra, `""` error) y evita ambigüedad de `""` en `spec.md:20`. RF-1/RF-4.

4. **Validación contacto sintáctica en `schemas` vs en `services`**
   - Elegida: `schemas` con regex y longitud (sin I/O).
   - Descartada: solo en `services` o con verificación de dominio/operador.
   - Motivo: principio 3, RNF-2, sin verificar dominio (duda resuelta); barato y da 422 inmediato. Decisión 3 de §5 en `001`. RF-1/RF-4.

5. **Teléfono conserva formato original vs normaliza a solo dígitos**
   - Elegida: conserva formato original (`+`/` ` `-`/`()`), valida por conteo de dígitos 7-15.
   - Descartada: normalizar a solo dígitos `E.164`.
   - Motivo: responde duda `spec.md:96`, preserva trazabilidad de entrada y es más simple para MVP; futura normalización no bloquea `003`. RF-1.

6. **`PATCH /proveedores/{codigo}` vs `PUT`**
   - Elegida: `PATCH` parcial (≥1 campo editable).
   - Descartada: `PUT` total.
   - Motivo: RF-4 permite editar `nombre` y/o contacto por separado; `PATCH` evita sobreescritura accidental de campos no enviados y permite `null` para borrar. RF-4.

7. **`codigo` `VARCHAR + CHECK` vs `ENUM`**
   - Elegida: `VARCHAR(20)` con `CHECK` regex.
   - Descartada: `ENUM` nativo.
   - Motivo: `codigo` es abierto (no cerrado como `categoria` en `001`), más fácil de migrar con Alembic. RF-1.

8. **Unicidad: `UNIQUE` DB + `IntegrityError` vs solo `SELECT` previo**
   - Elegida: ambas.
   - Descartada: solo `SELECT`.
   - Motivo: evita carrera concurrente (caso límite `spec.md:74`). RF-1.

## 6. Nota explícita para 003-movimientos-inventario

**Identificador expuesto:** `proveedores.id` `Integer` PK (autoincrement). `codigo` (`VARCHAR(20)` normalizado) es único de negocio pero **la FK usará `id`**, no `codigo`, para estabilidad (código inmutable pero `id` es interno y no cambia nunca).

**Esquema futuro en `movimientos_inventario`:**
```sql
proveedor_id INTEGER NOT NULL REFERENCES proveedores(id) ON DELETE RESTRICT
```
- Tipo: `Integer` (SQLAlchemy `ForeignKey("proveedores.id")`, `index=True`).
- Restricción: `ON DELETE RESTRICT` — impide borrar físicamente un proveedor referenciado (aunque no se borra nunca por RNF-1, es salvaguarda).
- Validación en `003` (service, no router): al crear movimiento `entrada`, `proveedor_service.obtener_por_codigo` o `obtener_por_id` debe verificar existencia y `estado == 'activo'`; si `inactivo` → `400` `Proveedor inactivo no utilizable`; si no existe → `404`. El listado de proveedores activos (`GET /proveedores`) sirve para selección, pero la validación de escritura debe hacerse por `id` en service de movimientos.
- Ejemplo fila `003` que referencia: `movimientos_inventario(proveedor_id=1, producto_id=1, tipo='entrada', cantidad=10)`.
- RF cubiertos: RF-5 (baja permite con movimientos previos pero inhabilita futuras) y RNF-5 (trazabilidad).

## 7. Plan de migración Alembic

**Revisión:** `alembic revision --autogenerate -m "crea proveedores"` → `alembic upgrade head` sin errores (principio 5).

**Cambios:**
- Crear tabla `proveedores` con columnas, checks e índices de §2.1.
- Índices: `ix_proveedores_codigo` `UNIQUE`, `ix_proveedores_estado`, `ix_proveedores_nombre` (opcional).
- No toca `productos` ni `movimientos_inventario` (migración inicial de T02/T03 ya en `63276eeea69c`).
- Verificación: `alembic upgrade head` y `alembic downgrade -1` + `upgrade` sin pérdida; `psql \d proveedores` muestra constraints.

## 8. Estrategia de tests

Sin escribir código de tests (principio 4: `pytest -v` verde).

**Unitarios — `services/proveedor_service.py` (mock `Session` / `sqlite:///:memory:`):**
- RF-1: alta válida sin contacto / con contacto completo → crea `activo`; duplicado exacto/normalizado (`prov-001` vs ` PROV-001 `) → 409; `codigo` 2/21, `*`, `nombre` 1/101, `email` sin `@`/`""`/`255`, `telefono` 6/16 dígitos/letras/`+` medio, `direccion` 4/201/`""` → 422; duplicado tras inactivo → 409; carrera `IntegrityError` → 409.
- RF-4: edición `nombre`/`email`/`telefono`/`direccion` parcial → actualiza; `codigo` distinto → 400, mismo → ignora; `estado` → ignora; `null` borra vs ausente no cambia vs `""` → 422; payload vacío → 422; inactivo → 400; no encontrado → 404.
- RF-5: baja activo → `inactivo`; ya inactivo → 400; no encontrado → 404; con movimientos previos → 200 (no valida).
- RF-2/RF-3: `listar_activos` solo `activos` ordenado por `codigo`; `obtener_por_codigo` normaliza y devuelve `inactivo` también; no encontrado → 404.

**Integración — `routers/proveedores.py` (`TestClient` + `TestSession`):**
- RF-1: `POST /api/v1/proveedores` `201` con `codigo` normalizado y contacto, `201` sin contacto (`null`), `409` duplicado (incluye inactivo), `422` validaciones.
- RF-2: `GET /api/v1/proveedores` `200` `[]` vacío y solo activos (inactivo excluido, sin `estado`).
- RF-3: `GET /api/v1/proveedores/{codigo}` `200` activo/inactivo con `estado`, `404` inexistente, normalizado (`  prov-001 `).
- RF-4: `PATCH /api/v1/proveedores/{codigo}` `200` borra con `null`, ignora ausente, `400` inmutable/inactivo, `404`, `422` validación/vacío.
- RF-5: `DELETE /api/v1/proveedores/{codigo}` `200` → `inactivo`, `400` ya inactivo, `404`, y posterior `GET` listado excluye pero detalle incluye; verificar que `003` futuro rechazaría entrada con `inactivo` (simulado via service).
- Transversal: mensajes en español, sin exponer modelos SQLAlchemy, `ruff`/`mypy` pasan, `GET /docs` lista 5 endpoints `/proveedores`.

Cada test mapea a su RF y RNF-1..RNF-5.

