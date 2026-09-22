# Tasks 002 — Gestión de Proveedores

> Orden por dependencias. Cada tarea 20-30 min. Constitución y `AGENTS.md` vigentes.

- [x] **T01 — Modelo `Proveedor` (tabla `proveedores`)** — RF-1, RF-4, RF-5
  - RF: RF-1 (definición), RF-4 (campos editables), RF-5 (estado)
  - Hecho cuando: `app/models/proveedor.py` define `Proveedor` con columnas `id, codigo VARCHAR(20) UNIQUE, nombre VARCHAR(100), email VARCHAR(254) NULL, telefono VARCHAR(20) NULL, direccion VARCHAR(200) NULL, estado, created_at, updated_at`, checks e índices según plan §2.1, y `mypy app` pasa.

- [x] **T02 — Schemas Pydantic `ProveedorCreate / ProveedorUpdate / ProveedorResponse`** — RF-1, RF-4
  - RF: RF-1, RF-4
  - Hecho cuando: `app/schemas/proveedor.py` valida `codigo 3-20 regex trim+upper`, `nombre 2-100 trim`, `email` sintáctico `trim+lower <=254`, `telefono` 7-15 dígitos con `+`/` ` `-`/`()`, `direccion` 5-200 trim, `null` borra vs ausente no cambia vs `""` → 422, `ProveedorUpdate` exige ≥1 de `nombre/email/telefono/direccion`, y `ruff check .` pasa.

- [x] **T03 — Service: alta `crear_proveedor()` con normalización y unicidad** — RF-1
  - RF: RF-1
  - Hecho cuando: `app/services/proveedor_service.py:crear_proveedor` normaliza `codigo trim+upper`/`email trim+lower`, rechaza duplicado incluyendo inactivos (409), valida `telefono` por dígitos, crea `activo` con contacto opcional; captura `IntegrityError` → 409, y `mypy app` pasa.

- [x] **T04 — Service: consultas `listar_activos()` y `obtener_por_codigo()`** — RF-2, RF-3
  - RF: RF-2, RF-3
  - Hecho cuando: `listar_activos()` devuelve solo `activos` ordenados por `codigo` con `codigo/nombre/email/telefono/direccion` (sin `estado`); `obtener_por_codigo()` normaliza `codigo` y devuelve `activo`/`inactivo` con `estado`; 404 si no existe.

- [x] **T05 — Service: edición `actualizar_proveedor()`** — RF-4
  - RF: RF-4
  - Hecho cuando: `actualizar_proveedor()` edita solo `nombre`/`email`/`telefono`/`direccion` de `activo`, `null` borra vs ausente no cambia vs `""` → 422, rechaza 404 no encontrado, 400 inactivo, 400 `codigo` distinto inmutable (mismo se ignora, `estado` se ignora).

- [x] **T06 — Service: baja lógica `baja_proveedor()`** — RF-5
  - RF: RF-5
  - Hecho cuando: `baja_proveedor()` marca `activo→inactivo`, rechaza 404 no encontrado y 400 ya inactivo, permite con movimientos previos sin validar, sin `DELETE` físico, y `mypy app` pasa.

- [x] **T07 — Router `POST /api/v1/proveedores`** — RF-1
  - RF: RF-1
  - Hecho cuando: `app/routers/proveedores.py` expone `POST` que delega a `crear_proveedor`, retorna 201 con `codigo` normalizado y `email` en minúsculas, 409 duplicado, 422 validación, sin lógica de negocio en router.

- [x] **T08 — Router `GET /api/v1/proveedores` listado** — RF-2
  - RF: RF-2
  - Hecho cuando: `GET` retorna 200 con lista de activos ordenada o `[]` si vacío, excluye inactivos, sin campo `estado`, delega a `listar_activos`.

- [x] **T09 — Router `GET /api/v1/proveedores/{codigo}` detalle** — RF-3
  - RF: RF-3
  - Hecho cuando: `GET` con `{codigo}` normalizado retorna 200 con `estado` (activo/inactivo), 404 si no existe, delega a `obtener_por_codigo`.

- [x] **T10 — Router `PATCH /api/v1/proveedores/{codigo}` edición** — RF-4
  - RF: RF-4
  - Hecho cuando: `PATCH` retorna 200 tras editar (soporta `null` para borrar), 404/400 según service, 422 payload vacío o validación, y `/docs` muestra schema correcto.

- [x] **T11 — Router `DELETE /api/v1/proveedores/{codigo}` baja lógica** — RF-5
  - RF: RF-5
  - Hecho cuando: `DELETE` retorna 200 con `estado=inactivo`, 404/400 según service, y posterior `GET` listado excluye pero detalle incluye `inactivo`.

- [x] **T12 — Registro del router en `app/main.py`** — RF-1..RF-5
  - RF: RF-1, RF-2, RF-3, RF-4, RF-5
  - Hecho cuando: `app/main.py` incluye `proveedores.router` junto a `productos.router` y `GET /openapi.json` lista 10 endpoints (5 de productos + 5 de proveedores) y `GET /docs` 200.

- [x] **T13 — Migración Alembic `crea proveedores`** — RF-1, RF-5
  - RF: RF-1, RF-5
  - Hecho cuando: `alembic revision --autogenerate -m "crea proveedores"` genera `xxxx_crea_proveedores.py` con tabla `proveedores`/`checks`/`índices` y `alembic upgrade head` y `downgrade -1` + `upgrade` pasan sin errores.

- [x] **T14 — Tests unitarios de service (mock + sqlite)** — RF-1..RF-5
  - RF: RF-1, RF-2, RF-3, RF-4, RF-5
  - Hecho cuando: tests cubren alta con/sin contacto y duplicado normalizado, email/teléfono/dirección `null`/ausente/`""`, edición `null` borra vs `""` rechaza, inmutable, inactivo, baja idempotencia, consultas filtradas y carrera `IntegrityError`; `pytest -v` unitarios en verde y `mypy app` pasa.

- [x] **T15 — Tests de integración de endpoints (TestClient + DB test)** — RF-1..RF-5
  - RF: RF-1, RF-2, RF-3, RF-4, RF-5
  - Hecho cuando: `POST/GET/PATCH/DELETE /api/v1/proveedores` verifican 201/200/400/404/409/422, `null` borra, inactivo excluido de listado pero visible en detalle, permite baja con movimientos y verifica que `003` futuro rechazaría entrada con `inactivo`; mensajes en español y sin exponer modelos; `pytest -v` integración en verde.

- [x] **T16 — Verificación final constitución + AGENTS.md** — RF-1..RF-5
  - RF: RF-1, RF-2, RF-3, RF-4, RF-5
  - Hecho cuando: `pytest -v` 100% verde, `ruff check .` y `ruff format .` sin errores, `mypy app` sin errores, `alembic upgrade head` ok, `GET /docs` lista 10 endpoints y `proveedor_id` expuesto como `Integer` para `003` .

