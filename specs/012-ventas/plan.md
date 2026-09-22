# Plan 012 — Registro de Ventas

> Constitución: `docs/constitution.md` principios 1-6 | Spec: `specs/012-ventas/spec.md` RF-1..RF-4 (versión corregida 12 decisiones) | Convenciones: `AGENTS.md` | Reutiliza `003-movimientos-inventario/plan.md` §4-6 (`registrar_salida` con `SELECT FOR UPDATE`) y `011-autenticacion/plan.md` §5 (`get_current_user` antes de BD)

## 1. Estructura de módulos afectados — [Cubre RF-1..RF-4 + RNF-5]

Respetando arquitectura por capas `routers/ → services/ → models/ + schemas/` y principios 1 y 3 (routers solo HTTP, services solo negocio; nunca reimplementar descuento de stock, `AGENTS.md:29`).

| Capa | Archivo | Acción | RF cubiertos | Responsabilidad |
|------|---------|--------|--------------|-----------------|
| `models/` | `app/models/venta.py` | **Crear** | RF-1, RF-2 | Entidad `Venta` (singular) tabla `ventas` — cabecera con cliente embebido, `total` y `created_at` |
| `models/` | `app/models/venta_item.py` | **Crear** | RF-1, RF-2 | Entidad `VentaItem` tabla `venta_items` — cada línea del carrito con `producto_id`, `cantidad`, `precio_unitario`, `subtotal` y `movimiento_id` FK a `movimientos_inventario` |
| `schemas/` | `app/schemas/venta.py` | **Crear** | RF-1, RF-3, RF-4 | Pydantic `VentaCreate` (cliente + items), `VentaResponse`/`VentaListResponse`, validación sintáctica sin BD; nunca expone `float` |
| `services/` | `app/services/venta_service.py` | **Crear** | RF-1, RF-2 | Orquestación: orden de validación de spec (1) formato sin BD `422` → (2) existencia `404` → (3) activo/stock `400`, cálculo `Decimal` y transacción atómica con invocación a `003` |
| `services/` | `app/services/movimiento_service.py` | **Reutilizar** | RF-2, RNF-1 | `registrar_salida` con `SELECT FOR UPDATE` ya validado en `003`; `012` lo invoca `N` veces ya autorizado, no lo modifica |
| `routers/` | `app/routers/ventas.py` | **Crear** | RF-1, RF-3, RF-4 | Endpoints `POST /api/v1/ventas`, `GET /api/v1/ventas`, `GET /api/v1/ventas/{id}` — solo HTTP + delegación a `venta_service`, protegidos con `Depends(get_current_user)` |
| `app/` | `app/main.py` | **Modificar** | RF-1..RF-4 | Registrar `ventas.router` con prefijo `/api/v1` (junto a `productos`/`proveedores`/`movimientos`/`stock`) |
| `alembic/` | `alembic/versions/xxxx_ventas_012.py` | **Crear** | RF-1, RF-2 | Migración que crea `ventas` y `venta_items` (ver §7) |

> Verificación principio 1 y `AGENTS.md:33`: `ruff check .`, `mypy app`, `pytest -v` verde con `Bearer`. No se toca `stock_service` ni cálculo de `003`.

## 2. Modelo de datos — [Cubre RF-1, RF-2, RNF-3]

### 2.1 Tabla `ventas` — cabecera
Modelo `Venta` → tabla `ventas` (plural). Cliente embebido como columnas propias (decisión §6).

| Columna | Tipo SQLAlchemy/PostgreSQL | Restricciones | Índice |
|---------|----------------------------|---------------|--------|
| `id` | `Integer` PK autoincrement | PK | PK |
| `created_at` | `DateTime(timezone=True)` | `NOT NULL DEFAULT now()` inmutable, `ISO 8601 Z` | `INDEX ix_ventas_created_at DESC` + `INDEX ix_ventas_id` implícito |
| `cliente_nombre` | `VARCHAR(100)` | `NOT NULL`, check `length(trim(cliente_nombre)) BETWEEN 2 AND 100` | — |
| `cliente_email` | `VARCHAR(254)` | `NULL`, check `cliente_email IS NULL OR length(cliente_email) <=254` (validación completa de formato `002` en `schemas`, no en DB) | — |
| `total` | `Numeric(12,2)` | `NOT NULL`, check `total >= 0` | — |

RF: RF-1 (cliente embebido, `created_at` servidor, `total` derivado). No hay `updated_at` (append-only, `RNF-3`).

### 2.2 Tabla `venta_items` — líneas del carrito
Modelo `VentaItem` → tabla `venta_items`. Cada fila es un producto distinto del carrito (1-20 por venta).

| Columna | Tipo | Restricciones | Índice/FK |
|---------|------|---------------|-----------|
| `id` | `Integer` PK | PK | PK |
| `venta_id` | `Integer` | `NOT NULL`, `FK ventas.id ON DELETE RESTRICT` | `INDEX ix_venta_items_venta_id` + FK |
| `producto_id` | `Integer` | `NOT NULL`, `FK productos.id ON DELETE RESTRICT` | `INDEX ix_venta_items_producto_id` |
| `cantidad` | `Integer` | `NOT NULL`, `CHECK cantidad > 0 AND cantidad <= 1000000` | — |
| `precio_unitario` | `Numeric(12,2)` | `NOT NULL`, `CHECK precio_unitario >= 0 AND precio_unitario <= 1000000` | — |
| `subtotal` | `Numeric(12,2)` | `NOT NULL`, `CHECK subtotal = cantidad * precio_unitario` (comentario, validado en service) | — |
| `movimiento_id` | `Integer` | `NULL` hasta crear movimiento, luego `NOT NULL`, `FK movimientos_inventario.id ON DELETE RESTRICT`, `UNIQUE` | `UNIQUE INDEX ix_venta_items_movimiento_id` |

RF: RF-1 (carrito 1-20, `SKU` duplicado detectado en `schemas` antes de BD, `cantidad` entera, `precio` Decimal 2 decimales, `subtotal` derivado), RF-2 (trazabilidad bidireccional `movimiento_id`).

- **Relación `movimientos_ids`:** no es columna `JSON`/`ARRAY` en `ventas`; es derivada como `ARRAY_AGG(venta_items.movimiento_id)` o `SELECT movimiento_id FROM venta_items WHERE venta_id=:id`. Se eligió tabla intermedia normalizada `venta_items` con `movimiento_id` FK (decisión §6) y no `ventas.movimientos_ids JSONB`.

### 2.3 Ejemplo de fila representativa

`ventas` + `venta_items` para venta con 2 productos:

```json
// ventas
{
  "id": 7,
  "created_at": "2026-09-21T14:30:00Z",
  "cliente_nombre": "Ana",
  "cliente_email": "ana@correo.com",
  "total": "45.50"
}
// venta_items
[
  {
    "id": 13,
    "venta_id": 7,
    "producto_id": 3,
    "cantidad": 2,
    "precio_unitario": "10.00",
    "subtotal": "20.00",
    "movimiento_id": 42
  },
  {
    "id": 14,
    "venta_id": 7,
    "producto_id": 5,
    "cantidad": 1,
    "precio_unitario": "25.50",
    "subtotal": "25.50",
    "movimiento_id": 43
  }
]
```
`total "45.50"` = `20.00 + 25.50`, ambos `Decimal`. `movimiento_id` 42 y 43 son `salida` en `movimientos_inventario` creados vía `003`. Con `cliente_email` `null`/ausente, `cliente_email` sería `null` en `ventas`.

## 3. Contrato de la API — [Cubre RF-1, RF-2, RF-3, RF-4, RNF-5]

Base: `/api/v1` (`AGENTS.md:21`). JSON `Content-Type: application/json`. Mensajes en español (`RNF-4`). Todos requieren `Authorization: Bearer <token>` salvo error `401` antes de BD (`011`).

### RF-1 — `POST /api/v1/ventas` (protegido, sin barra final)

**Request 201 (éxito, 2 ítems):**
```json
POST /api/v1/ventas
Authorization: Bearer <token>
{
  "cliente": {"nombre": "  Ana  ", "email": "ANA@correo.com"},
  "items": [
    {"producto_codigo": "  prod-001 ", "cantidad": 2, "precio_unitario": "10.00"},
    {"producto_codigo": "PROD-002", "cantidad": 1, "precio_unitario": "25.50"}
  ]
}
```
Normalización: `cliente.nombre` → `Ana` (`trim`), `cliente.email` → `ana@correo.com` (`trim+lower`), `producto_codigo` → `PROD-001`/`PROD-002` (`trim+upper`) antes de validar formato.

**Response 201:**
```json
{
  "id": 7,
  "created_at": "2026-09-21T14:30:00Z",
  "cliente": {"nombre": "Ana", "email": "ana@correo.com"},
  "items": [
    {"producto_codigo": "PROD-001", "cantidad": 2, "precio_unitario": "10.00", "subtotal": "20.00"},
    {"producto_codigo": "PROD-002", "cantidad": 1, "precio_unitario": "25.50", "subtotal": "25.50"}
  ],
  "total": "45.50",
  "movimientos_ids": [42, 43]
}
```
Si el cliente envía `total`, `subtotal`, `created_at` o `id` en el request, se ignoran silenciosamente (no `422`).

**Errores RF-1 (orden de validación §5):**
- `422` formato/estructura sin BD: `{"cliente": null}` o ausente, `cliente.nombre` `""`/1/101, `cliente.email ""` (vacío tras trim), `items: []`/`null`/ausente, `items` >20, `producto_codigo` formato 3-20 inválido tras normalización, `SKU` duplicado tras normalización (`PROD-001` y ` prod-001 `), `cantidad` `0`/`-1`/`1.5`/`"2"`/`2.00`/`1_000_001`, `precio_unitario` `"-0.01"`/`"10.00"` (string)/`10.123`/`1_000_000.01`/`null` → `422` con `detail` que indica `items[1].cantidad` o `producto_codigo` duplicado.
- `404` existencia: `producto_codigo` no encontrado → `404 {"detail": "Producto no encontrado: PROD-999"}` (primero en fallar según orden).
- `400` inactivo/stock: `producto` `inactivo` → `400 {"detail": "Producto inactivo: PROD-002"}`, `stock insuficiente` → `400 {"detail": "Stock insuficiente para el producto PROD-002: disponible 3, solicitado 5"}`.

### RF-3 — `GET /api/v1/ventas` (listado, protegido, sin barra final)

**Request:**
```
GET /api/v1/ventas
Authorization: Bearer <token>
```

**Response 200 (con ventas, orden `created_at DESC, id DESC`):**
```json
[
  {
    "id": 7,
    "created_at": "2026-09-21T14:30:00Z",
    "cliente": {"nombre": "Ana", "email": "ana@correo.com"},
    "items": [{"producto_codigo": "PROD-001", "cantidad": 2, "precio_unitario": "10.00", "subtotal": "20.00"}],
    "total": "20.00",
    "movimientos_ids": [42]
  }
]
```

**Response 200 vacío:**
```json
[]
```

**Errores:**
- Sin `Bearer` o inválido/expirado → `401` antes de BD (como `011`).

### RF-4 — `GET /api/v1/ventas/{id}` (detalle, protegido)

**Request:**
```
GET /api/v1/ventas/7
Authorization: Bearer <token>
```

**Response 200 (existe):**
```json
{
  "id": 7,
  "created_at": "2026-09-21T14:30:00Z",
  "cliente": {"nombre": "Ana", "email": "ana@correo.com"},
  "items": [{"producto_codigo": "PROD-001", "cantidad": 2, "precio_unitario": "10.00", "subtotal": "20.00"}],
  "total": "20.00",
  "movimientos_ids": [42]
}
```

**Errores:**
- `id` no existe → `404 {"detail": "Venta no encontrada"}`
- Sin `Bearer` → `401` antes de BD

**Resumen códigos:**
| Endpoint | 200 | 201 | 401 | 404 | 400 | 422 |
|----------|-----|-----|-----|-----|-----|-----|
| POST /ventas |  | RF-1 éxito | RF-5 sin/inválido Bearer | RF-2 no encontrado | RF-2 inactivo/stock insuficiente | RF-1 validación formato/duplicado |
| GET /ventas | RF-3 |  | RF-3 |  |  |  |
| GET /ventas/{id} | RF-4 |  | RF-4 | RF-4 no existe |  |  |

## 4. Diseño de la transacción atómica — [Cubre RF-2, RNF-2]

**Pseudocódigo del flujo completo en `venta_service.registrar_venta(db, datos, usuario_email)` dentro de una sola transacción (no reimplementa descuento, solo orquesta):**

```
BEGIN (Session con autocommit=False)
# 1) Validación de formato/estructura sin BD ya pasó en schemas (422). Solo queda validar duplicado tras normalización
normalizar cada producto_codigo (trim+upper) y detectar duplicados en carrito → si duplicado → rollback, 422
# 2) Validación contra BD — existencia y activo (404/400)
para cada item en carrito:
    producto = SELECT * FROM productos WHERE sku = :codigo_norm  # sin lock aún, solo existencia
    si no existe → rollback, 404 con producto_codigo
    si producto.estado != 'activo' → rollback, 400 con producto_codigo
# 3) Validación de stock propia de ventas, leyendo stock actual directamente ANTES de invocar 003
para cada item:
    stock_actual = calcular_stock_actual(producto.id)  # SELECT SUM(cantidad) FILTER (tipo='entrada'/'salida') + stock_inicial, con SELECT FOR UPDATE del producto para serializar
    si cantidad > stock_actual → rollback, 400 específico con disponible/solicitado y producto_codigo
# Si alguna validación falla → rollback total, no se persiste nada (ni venta, ni movimientos, ni movimientos_ids) — RNF-2 y persistencia en fallo de spec
# 4) Solo si todas las validaciones pasaron, invocar N veces a 003 ya autorizado
movimientos_ids = []
para cada item:
    movimiento = movimiento_service.registrar_salida(db, MovimientoCreateSalida(producto_codigo, cantidad, motivo="venta #<id provisional>"))
    # movimiento_service ya hace su propio SELECT FOR UPDATE y validación, pero como ya validamos, no fallará por stock; si fallara por carrera, capturamos y rollback
    movimientos_ids.append(movimiento.id)
# 5) Crear venta y items con totales derivados Decimal
venta = INSERT INTO ventas (cliente_nombre, cliente_email, total, created_at) VALUES (...)
para cada item:
    subtotal = cantidad * precio_unitario (Decimal, 2 decimales)
    INSERT INTO venta_items (venta_id, producto_id, cantidad, precio_unitario, subtotal, movimiento_id)
total = sum(subtotal)
venta.total = total
COMMIT
retornar venta con movimientos_ids
EXCEPT cualquier HTTPException o IntegrityError → ROLLBACK total, propagar 404/400/422
```

**Notas:**
- `calcular_stock_actual` es la misma función compartida entre `003` y `012` (extraída a `stock_service` o importada de `movimiento_service`), no duplicada, para no violar `AGENTS.md:29`.
- La validación de stock propia de ventas lee directamente `stock_actual` con `SELECT FOR UPDATE` del producto (como en `003`), pero el mensaje `Stock insuficiente para X: disponible 3, solicitado 5` lo construye ventas, no `003` (decisión 5).
- `003.registrar_salida` se invoca recién después de que todas las validaciones de venta pasaron, exclusivamente para ejecutar el descuento atómico ya autorizado, dentro de la misma `Session`/`BEGIN` (no se abre nueva transacción).

> RF-2 (atomicidad y orden), RNF-2 (transacción única), RNF-1 (reutilización 003).

## 5. Reglas de validación: schema vs service — [Cubre RF-1, RF-2, orden de validación]

**Principio 3:** `routers/` solo HTTP, `schemas/` sintáctica sin I/O, `services/` negocio con BD.

**En `schemas/venta.py` (Pydantic) — sintáctica, sin I/O, `422` antes de BD (etapa 1 del orden):**
- `cliente.nombre` `trim` 2-100, `cliente.email` `Optional` con `trim+lower` y regex `002` (`""` tras trim → 422, `null`/ausente → None), `cliente` y `items` requeridos (ausentes/`null` → 422).
- `items` `list` 1-20, `producto_codigo` `trim+upper` `^[A-Z0-9_-]{3,20}$`, `cantidad` `StrictInt` `1..1_000_000` con `strict=True` (rechaza `2.00`, `1.5`, `"2"`), `precio_unitario` `Decimal` con `max_digits` y `decimal_places=2` y `ge=0 le=1000000` (rechaza `>2` decimales, `>1_000_000`, string, `float`), `SKU` duplicado tras normalización detectado con `model_validator` → 422.
- `total`/`subtotal`/`created_at`/`id` no definidos en `VentaCreate` (se ignoran si se envían, se usa `Config extra="ignore"`), nunca `422` por ellos.
- Justificación: declarativas, baratas, 422 inmediato sin abrir transacción.

**En `services/venta_service.py` — negocio con BD, `404`/`400` (etapas 2 y 3 del orden):**
- `producto` no existe (por `producto_codigo` normalizado) → `404` con `producto_codigo`; `producto.estado != 'activo'` → `400` con `producto_codigo`.
- `cantidad > stock_actual` (leído con `SELECT FOR UPDATE`) → `400` con `disponible`/`solicitado` y `producto_codigo`.
- `stock_actual` se lee directamente (no se delega aún a `003` para validar), pero el descuento sí se delega a `003` después.
- Justificación: requieren estado persistido y `SELECT FOR UPDATE`; no pertenecen a `schemas`.

> Orden de validación de spec: primero `schemas` (`422`), luego existencia (`404`), luego activo/stock (`400`) — define prioridad de status.

## 6. Decisiones técnicas justificadas — [Cubre RF-1, RF-2, RNF-3]

1.  **Cliente embebido como columnas propias vs `JSONB`**
    - Elegida: `ventas.cliente_nombre` `VARCHAR(100)` + `ventas.cliente_email` `VARCHAR(254) NULL`.
    - Descartada: `cliente JSONB` `{"nombre": "...", "email": "..."}`.
    - Motivo: `cliente` tiene solo 2 campos fijos, sin anidamiento; columnas permiten `CHECK` y `INDEX` simple y `SELECT` sin parseo JSON, y es consistente con `002` (proveedor tiene columnas separadas). `JSONB` añadiría complejidad de validación y no se necesita para búsquedas por cliente (fuera de alcance sin filtros). RF-1.

2.  **Referencia `movimientos_ids` como tabla `venta_items.movimiento_id` vs columna `ventas.movimientos_ids INTEGER[]`/`JSONB`**
    - Elegida: `venta_items.movimiento_id` `FK` único a `movimientos_inventario.id` (relación 1:1 por ítem), `movimientos_ids` derivado como `ARRAY_AGG`.
    - Descartada: `ventas.movimientos_ids INTEGER[]` o `JSONB [42,43]`.
    - Motivo: normalizada, permite `FOREIGN KEY` con `ON DELETE RESTRICT` y `UNIQUE` para evitar duplicados, y trazabilidad bidireccional `venta → movimiento` vía `JOIN` sin parseo de array; `ARRAY`/`JSONB` no permite `FK` y complica `rollback` atómico. RF-2, RNF-3.

3.  **`venta_items` tabla separada vs `items` JSONB en `ventas`**
    - Elegida: tabla separada `venta_items` (1:N).
    - Descartada: `ventas.items JSONB` con array de objetos.
    - Motivo: `items` requiere validación de `cantidad`/`precio`/`subtotal` como `Decimal` y `FK` a `producto_id` y `movimiento_id`; tabla permite `CHECK` y `INDEX` por `producto_id` y evita duplicar lógica de `SKU` duplicado en JSON. RF-1.

4.  **`total`/`subtotal` como `Numeric(12,2)` vs `Float`**
    - Elegida: `Numeric(12,2)` con `Decimal` en Pydantic (`Strict` con `decimal_places=2`).
    - Descartada: `Float`/`Double Precision`.
    - Motivo: evita errores de redondeo de `float` (RNF-6), crítico para `total == sum(cantidad*precio)` exacto; `Numeric` es estándar para moneda.

5.  **`created_at` como `DateTime(timezone=True)` con `Z` vs `String`**
    - Elegida: `DateTime(timezone=True)` con `server_default=now()` y serialización `ISO 8601 Z`.
    - Descartada: `VARCHAR` con fecha enviada por cliente.
    - Motivo: `created_at` nunca enviado por cliente (RF-1), generado por servidor con `timezone.utc` y `Z`, inmutable y ordenable `DESC`.

## 7. Plan de migración Alembic — [Cubre RF-1, RF-2]

**Revisión:** `alembic revision --autogenerate -m "crea ventas 012"` → `alembic upgrade head` sin errores (principio 5, `AGENTS.md:36`).

**Cambios (única migración de 012):**
- Crear tabla `ventas` con `id PK`, `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `cliente_nombre VARCHAR(100) NOT NULL CHECK length(trim(cliente_nombre)) BETWEEN 2 AND 100`, `cliente_email VARCHAR(254) NULL`, `total NUMERIC(12,2) NOT NULL CHECK total >=0`, índices `ix_ventas_created_at DESC` y `ix_ventas_id`.
- Crear tabla `venta_items` con `id PK`, `venta_id FK ventas.id ON DELETE RESTRICT`, `producto_id FK productos.id ON DELETE RESTRICT`, `cantidad INTEGER CHECK >0 AND <=1000000`, `precio_unitario NUMERIC(12,2) CHECK >=0 AND <=1000000`, `subtotal NUMERIC(12,2)`, `movimiento_id FK movimientos_inventario.id ON DELETE RESTRICT UNIQUE`, índices `ix_venta_items_venta_id`, `ix_venta_items_producto_id`, `ix_venta_items_movimiento_id` único.
- No modifica `productos`, `proveedores`, `movimientos_inventario`, `usuarios` (ya en `63276eeea69c`, `37840112ca70`, `9111dba96a53`, `ff5b41c7a385`); si `ventas` ya existe, migración es no-op.
- Verificación: `alembic upgrade head` y `alembic downgrade -1` + `upgrade` sin pérdida; `psql \d ventas` y `\d venta_items` muestran `FK`, `CHECK` y `UNIQUE`.

## 8. Estrategia de tests — [Cubre RF-1..RF-4, RNF-1..RNF-8]

Sin escribir código de tests (principio 4: `pytest -v` verde).

**Unitarios — `services/venta_service.py` (mock `Session` / `sqlite:///:memory:` con `Base.metadata.create_all`):**
- RF-1: `cliente` sin `nombre`/`nombre` 1/101/`""` → 422, `email` `sinarroba`/`""` → 422, `null`/ausente → sin email; `items` `[]`/`null`/ausente/`21` → 422, `SKU` duplicado tras normalización (`PROD-001` vs ` prod-001 `) → 422, `producto_codigo` `AB`/`A*21` → 422, `cantidad` `0`/`-1`/`1.5`/`"2"`/`2.00`/`1_000_001` → 422, `precio` `-0.01`/`1_000_000.01`/`10.123`/`"10.00"` → 422, `10.50`/`10.5`/`10`/`0.00` → ok con `Decimal`.
- RF-1: `total`/`subtotal`/`created_at`/`id` enviados → ignorados, se persiste derivado con `Decimal`.
- RF-2: existencia `producto` no encontrado → 404 con `producto_codigo`, `inactivo` → 400, `stock` insuficiente `cantidad > stock_actual` → 400 con `disponible`/`solicitado`, sin crear venta ni movimientos (verifica `COUNT(*)` en `ventas` y `venta_items` y `stock_actual` no cambió).
- RF-2 atomicidad: venta con `PROD-A` stock 10 pide 5 OK y `PROD-B` stock 3 pide 5 falla → `400` y `stock_actual` de `PROD-A` sigue 10; concurrencia dos ventas con mismo `SKU` stock 10 pide 6 cada una con `SELECT FOR UPDATE` → una `201` otra `400` sin `stock_actual <0`.
- RF-2 reutilización: `registrar_salida` de `003` es invocado `N` veces solo después de validar; si se validó, `N` movimientos `salida` existen con `proveedor_id` null y `motivo` derivado de venta.

**Integración — `routers/ventas.py` (`TestClient` + `TestSession` con `productos`/`proveedores` creados via `POST` previos y `Bearer` de `011`):**
- RF-1: `POST /api/v1/ventas` `201` con cliente normalizado y carrito 1-20, `422` para `[]`/`>20`/duplicado/`cantidad`/`precio`/`cliente`, `201` con `total` enviado ignorado, verifica `created_at` con `Z` y `movimientos_ids` con 2 IDs y `Decimal` como string `"10.00"`.
- RF-2: `POST /ventas` con `SKU` no existe → `404`, `inactivo` → `400`, `stock insuficiente` → `400` con `disponible`/`solicitado` y sin venta ni movimientos, y sin dejar stock parcial (verifica `GET /stock` antes/después).
- RF-3: `GET /api/v1/ventas` `200` `[]` vacío y con 3 ventas orden `created_at DESC, id DESC`, sin `Bearer` → `401` antes de BD, con token → `200` sin exponer `password`.
- RF-4: `GET /api/v1/ventas/{id}` `200` con `movimientos_ids` que existen en `GET /movimientos`, `404` no existe, sin `Bearer` → `401` antes de BD.
- Transversal: sin `PUT`/`PATCH`/`DELETE` sobre `ventas` (`405`), `ruff`/`mypy` pasan, `GET /docs` lista 3 endpoints nuevos de ventas.

Cada test mapea a su RF y `RNF-1..RNF-8` y hereda `RNF-8` de `011` (sin rate limiting).

## 9. Cobertura de RFs — trazabilidad

| Parte del plan | RF cubierto | Evidencia verificable | Reutilizado de `003`/`011` |
|---|---|---|---|
| Modelo `ventas` con `cliente_nombre`/`cliente_email` como columnas + `total` | RF-1 | `cliente` `""`→`422`, `null`→`null`, `total` derivado | Propia + `002` formato email |
| Modelo `venta_items` con `producto_id`, `cantidad`, `precio_unitario`, `subtotal`, `movimiento_id` FK | RF-1, RF-2 | `cantidad` `2.00`→`422`, `precio` `10.123`→`422`, `SKU` duplicado→`422`, `movimiento_id` único | Propia |
| `venta_service` orden `422` → `404` → `400` | RF-1, RF-2 | `[]`→`422`, no existe→`404`, stock→`400` con detalle | Propia + `003` orden |
| `venta_service` `total`/`subtotal` ignorados y recalculados `Decimal` | RF-1 | `total` enviado `1.00` ignorado, `total` persiste `45.50` | Propia |
| `venta_service` validación propia de stock con `SELECT FOR UPDATE` antes de `003` | RF-2 | `stock` insuficiente `400` con `disponible/solicitado`, mensaje de ventas | Propia + `003` `SELECT FOR UPDATE` |
| `venta_service` invocación `N`×`registrar_salida` en misma transacción | RF-2, RNF-2 | `201` con `N` movimientos, `400` sin venta ni movimientos, concurrencia `201`/`400` | Sí (`003`) |
| `POST /ventas` `201` con `created_at` `Z` y `movimientos_ids` | RF-1 | `id` autoincrement, `created_at` `Z`, `movimientos_ids` con `N` IDs | Propia |
| `GET /ventas` y `GET /ventas/{id}` con `Bearer` antes de BD | RF-3, RF-4, RNF-5 | sin `Bearer`→`401` antes de `SELECT`, con token→`200` | Sí (`011` `get_current_user`) |
| `openapi.json` con 3 endpoints ventas y sin `PUT`/`DELETE` | RF-1, RF-3, RF-4 | `POST`/`GET`/`GET/{id}` presentes, `PUT`/`PATCH`/`DELETE` ausentes `405` | Propia |
| Migración `crea ventas` | RF-1, RF-2 | `ventas` + `venta_items` con `FK` y `CHECK` | Propia |
| Tests unitarios `venta_service` | RF-1, RF-2, RNF-6 | `Decimal` 2 decimales, nunca `float`, `422`/`404`/`400` sin efecto | Propia |
| Tests integración `ventas` | RF-1..RF-4 | `201`/`422`/`404`/`400`/`401` con `Bearer`, orden `created_at DESC` | Propia + `011` |

## 10. Fuera de alcance del plan (confirmado, spec.md:91-100)

No se diseña cancelación/devolución, edición/borrado, descuentos/impuestos/pagos, reservas, reutilización de cliente, campos `teléfono`/`avatar`, roles, paginación, filtros, valorización, auditoría por usuario — tal como `spec.md:91-100`.

## 11. Dudas abiertas

- Ninguna bloqueante. Queda como `[NECESITA ACLARACIÓN]` para specs futuros si se introduce tabla `clientes` y si `GET /ventas` debe paginarse con `limit/offset` o cursor `created_at+id`.

