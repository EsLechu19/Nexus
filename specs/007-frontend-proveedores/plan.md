# Plan 007 — Frontend Proveedores (Gestión de Catálogo)

## 1. Alineación con constitución y AGENTS — [Cubre todos RF]

- Respeta `frontend/docs/constitution.md:3` stack mínimo (React 18 + Vite + Tailwind + fetch) — sin estado global para RF-1..5, idéntica a `006/plan.md:1`.
- Respeta `frontend/docs/constitution.md:5` API aislada — todo HTTP en `src/api/proveedores.js` vía `src/api/client.js` de `005`; ningún `.jsx` hace `fetch` — RF-1..5, idéntica a `006`.
- Respeta `frontend/docs/constitution.md:7` estado servidor no cacheado — listado revalidado tras alta/edición/baja, sin `localStorage` — RF-1, RF-5, idéntica a `006`.
- Respeta `frontend/docs/constitution.md:8` idioma español — mensajes genéricos de `005` + 4xx de `002` ya en español — RF-5, idéntica a `006`.
- Respeta `frontend/AGENTS.md:20` centralización `src/api/proveedores.js` y `AGENTS.md:28` validación solo forma — RF-2..4, idéntica a `006`.
- Reutiliza `specs/005-frontend-base/plan.md:3-4,6` cliente `request` tipado (`validacion` vs `conexion`) y `Loading`/`ErrorMessage`/`EmptyState` — RF-1, RF-5, idéntica a `006`.
- Reutiliza patrón `specs/006-frontend-productos/plan.md:2-7` (listado 4-5 cols + modal reutilizado + diálogo baja + hook + banner 3s) — RF-1..5, adaptado a 5 campos proveedor.
- Contratos exactos `specs/002-proveedores/plan.md:3` (endpoints `/api/v1/proveedores`, códigos 201/200/400/404/409/422, normalización `codigo`/`email`, `null` vs ausente vs `""`) — RF-1..5, **propia** de este spec (proveedor).

## 2. Estructura de componentes dentro de `frontend/src/` — [Cubre RF-1..5]

```
frontend/src/
├── api/
│   ├── client.js                 # existente 005 — RF-3
│   ├── productos.js              # existente 006 — RF-1..5 productos
│   └── proveedores.js            # nuevo — RF-1..5 — ver §3 (idéntica a productos.js, propia)
├── pages/
│   ├── Productos.jsx             # existente 006 — RF-1..5 productos
│   ├── Proveedores.jsx           # nuevo — RF-1..5 — orquesta listado, modales, revalidación (idéntica a Productos.jsx, propia)
│   ├── PlaceholderPage.jsx       # existente 005 — RF-2 placeholders
│   └── NotFoundPage.jsx          # existente 005
├── components/
│   ├── ProveedorTabla.jsx        # nuevo — RF-1 — tabla 5 cols (codigo/nombre/email/telefono/direccion), "—" para null (propia, análoga a ProductoTabla)
│   ├── ProveedorFormModal.jsx    # nuevo — RF-2, RF-3 — modal reutilizado alta/edición, codigo deshabilitado en edición, botón Borrar para null (propia, análoga a ProductoFormModal + semántica null)
│   ├── ProveedorBajaDialog.jsx   # nuevo — RF-4 — diálogo confirmación baja (idéntica a ProductoBajaDialog, propia)
│   └── (reutilizados tal cual 005/006) Loading.jsx, ErrorMessage.jsx, EmptyState.jsx, ConfigErrorBanner.jsx — RF-1, RF-5
├── hooks/
│   ├── useProductos.js           # existente 006
│   └── useProveedores.js         # nuevo — RF-1, RF-5 — ver §4 (idéntica a useProductos, propia)
└── App.jsx                       # existente — añadir ruta /proveedores → Proveedores.jsx — RF-1 (idéntica a 006)
```

Responsabilidad — **qué se reutiliza tal cual de `006` vs qué es propio:**
- **Reutilizado tal cual (sin tocar):** `Loading.jsx`, `ErrorMessage.jsx`, `EmptyState.jsx`, `ConfigErrorBanner.jsx`, `AppLayout.jsx`/`NavLinkItem.jsx`, `client.js`, patrón `useProductos` → `useProveedores` (misma forma, distinto recurso), `App.jsx` con `BrowserRouter` future flags.
- **Propio (análogo a 006 pero con campos proveedor):** `Proveedores.jsx` (idéntica a `Productos.jsx` cambiando `useProveedores` + 5 cols), `ProveedorTabla.jsx` (análoga a `ProductoTabla.jsx` pero 5 cols y "—" para `null`), `ProveedorFormModal.jsx` (análoga a `ProductoFormModal.jsx` pero 5 campos + semántica `null`/`ausente`/`""` + botón Borrar), `ProveedorBajaDialog.jsx` (idéntica a `ProductoBajaDialog.jsx` cambiando texto), `src/api/proveedores.js` y `src/hooks/useProveedores.js` (idénticos a productos pero con `codigo`).

> Verificación constitución §3: `grep -r "fetch(" src/components src/pages src/hooks` vacío; solo `src/api/` contiene `fetch` — idéntica a `006`.

## 3. Consumo de endpoints vía cliente centralizado 005 — [Cubre RF-1..5] — *Propia (análoga a 006 §3)*

`src/api/proveedores.js` importa `request` de `src/api/client.js` (valida `VITE_API_URL`, `AbortController` 10s, headers JSON, tipa `validacion` vs `conexion`). Misma forma que `src/api/productos.js` de `006`, distinta ruta y semántica `null`.

```js
// src/api/proveedores.js — forma (análoga a productos.js)
export function listarProveedores() // GET /api/v1/proveedores → RF-1
export function crearProveedor({ codigo, nombre, email, telefono, direccion }) // POST → RF-2
export function editarProveedor(codigo, { nombre, email, telefono, direccion }) // PATCH → RF-3, semántica null/ausente
export function bajaProveedor(codigo) // DELETE → RF-4
```

Ejemplo por operación (contrato `002/plan.md:3`):

**RF-1 GET listado — `listarProveedores()`**
- Request: `GET /api/v1/proveedores` (`request('/api/v1/proveedores')`)
- Response 200: `[{"codigo":"PROV-001","nombre":"Distribuidora Central","email":"contacto@central.com","telefono":"+34 912","direccion":"Calle 10"}, {"codigo":"PROV-002","nombre":"Mayorista Norte","email":null,"telefono":null,"direccion":null}]` → mapeo directo a tabla, `null`→"—"
- Response 200 vacío: `[]` → `EmptyState`
- Orden por `codigo` garantizado por backend, frontend no reordena.

**RF-2 POST alta — `crearProveedor({codigo, nombre, email, telefono, direccion})`**
- Request: `POST /api/v1/proveedores` body `{"codigo":"  prov-001 ","nombre":"Distribuidora Central","email":"  CONTACTO@central.com ","telefono":"+34 912","direccion":"Calle 10"}` → `email` normalizado a minúsculas por backend, `codigo` a `PROV-001`
- Body sin contacto: `{"codigo":"PROV-002","nombre":"Mayorista Norte"}` (campos opcionales omitidos → `null`, sin traza, idéntico a `stock_inicial` ausencia en `006`)
- Body con `email: null` explícito no se usa en alta (alta con `null` es igual a omitir, pero se permite)
- Response 201: `{"codigo":"PROV-001","nombre":"...","email":"contacto@central.com",...,"estado":"activo"}`
- Error 409 duplicado (incluye inactivo) / 422 validación `email`/`telefono`/`direccion` → `validacion` sin Reintentar; 5xx/red → `conexion` con Reintentar

**RF-3 PATCH edición — `editarProveedor(codigo, {nombre, email, telefono, direccion})`**
- Request: `PATCH /api/v1/proveedores/PROV-001` body `{"nombre":"Central SL","email":null}` → `null` borra, ausente deja igual, `""` nunca se envía (bloqueado local)
- Body sin cambios: `{}` nunca se envía (bloqueado local como "Sin cambios")
- Response 200: mismo shape con `email:null`
- Error 400 `codigo` distinto, `payload vacío` → `validacion`; 404 no encontrado, 400 inactivo → `validacion`

**RF-4 DELETE baja — `bajaProveedor(codigo)`**
- Request: `DELETE /api/v1/proveedores/PROV-001`
- Response 200: `{"codigo":"PROV-001","estado":"inactivo",...}`
- Error 400 ya inactivo, 404 → `validacion` (permite aunque tenga movimientos, `003` validará después)

> Todas usan `VITE_API_URL` vía `client.js` sin hardcodeo — idéntica a `006`.

## 4. Modelo de estado local — [Cubre RF-1..5, RNF-3] — *Idéntica a 006 §4*

`Proveedores.jsx` + `useProveedores.js` viven solo en memoria, revalidan tras mutación — idéntica a `Productos.jsx`/`useProductos.js` de `006`, distinta entidad.

```js
// forma del estado en Proveedores.jsx (idéntica a Productos.jsx, propia)
{
  proveedores: [],            // Array<{codigo,nombre,email,telefono,direccion}> — RF-1
  cargandoListado: false,     // boolean — RF-1
  errorListado: null,         // {tipo,mensaje,reintentable}|null — RF-1
  modal: { abierto: false, modo: 'alta'|'edicion', proveedor: null }, // RF-2, RF-3
  dialogoBaja: { abierto: false, proveedor: null }, // RF-4
  operacion: { tipo: null|'alta'|'edicion'|'baja', cargando: false, error: null }, // RF-2..5
  mensajeExito: null          // "Proveedor creado/actualizado/dado de baja correctamente" — RF-2..4, 3s
}
```

`useProveedores.js` expone — idéntica a `useProductos.js`:
- `proveedores, cargandoListado, errorListado, revalidar()` — RF-1
- `crear(payload)` → `POST` → `revalidar()` — RF-2 (con `null`/ausente/`""` ya filtrado por modal)
- `editar(codigo, {nombre,email,telefono,direccion})` → `PATCH` → `revalidar()` — RF-3 (con `null` para borrar)
- `baja(codigo)` → `DELETE` → `revalidar()` — RF-4
- Nunca cachea `localStorage` (constitución §5) — idéntica.

## 5. Contrato de validación de formulario — [Cubre RF-2, RF-3, RNF-1] — *Propia (extendida vs 006 §5)*

**Frontend valida solo forma/UX, fuente de verdad es API (`AGENTS.md:28`) — idéntica filosofía a `006`, distinta semántica `null`/ausente:**

| Campo | Regla forma frontend (sin API) | Mensaje local | Regla negocio backend (API `002`) | Mensaje API |
|-------|-------------------------------|---------------|-----------------------------------|-------------|
| `codigo` | requerido tras `trim` | "Código requerido" | `3-20` `^[A-Z0-9_-]{3,20}$` tras `trim+mayúsculas` solo extremos, único global incluye inactivos | `409` "Código ya existe" o `422` longitud/formato |
| `nombre` | requerido tras `trim` | "Nombre requerido" | `2-100` tras `trim` | `422` "Nombre 2-100" |
| `email` | si informado y no es `null`, no debe quedar vacío tras `trim` (`""`/`"   "` → bloquea) | "No puede quedar vacío" | `trim+lower` `local@domino` `<=254`, `""`→422, `null`/ausente→NULL | `422` |
| `telefono` | si informado, no vacío tras `trim` | "No puede quedar vacío" | `trim` 7-15 dígitos, `+` solo inicio, `null`/ausente→NULL, `""`→422 | `422` |
| `direccion` | si informado, no vacío tras `trim` | "No puede quedar vacío" | `trim` 5-200, `null`/ausente→NULL, `""`→422 | `422` |

- Frontend nunca valida unicidad `codigo`, longitud exacta, regex email/teléfono, ni `trim+mayúsculas` más allá de `trim` para requerido; esos 4xx se muestran tal cual vienen de `002` (en español por `002` RNF-2) — **idéntica a `006`**.
- **Propia vs `006`:** en `006` `stock_inicial` vacío→ausencia; aquí `email`/`telefono`/`direccion` tienen triple semántica: `""`/`"   "` → bloquea local sin `fetch`, `null` explícito (vía botón "Borrar" en modal) → envía `null` para borrar, ausente (campo no tocado) → no se envía y conserva. En `006` no existe `null` para borrar.
- En edición, `codigo` deshabilitado y excluido del payload — **idéntica a `006` SKU**.

## 6. Flujo de cada operación (pseudocódigo) — [Cubre RF-1..5, RNF-2] — *Idéntica a 006 §6, adaptada a 5 campos*

**RF-1 Listado — `Proveedores.jsx` + `useProveedores.js`** — *Idéntica a `006`*
```
al montar: cargandoListado=true → <Loading />
  GET /proveedores → [] → <EmptyState> "Sin datos disponibles"
                → 4xx → <ErrorMessage validacion> sin Reintentar (con "—" para null ya mapeado)
                → conexion/5xx → <ErrorMessage conexion onReintentar=revalidar />
  éxito → <ProveedorTabla> 5 cols (codigo/nombre/email/telefono/direccion con "—")
```

**RF-2 Alta — `ProveedorFormModal` modo alta** — *Análoga a `006` alta, con 5 campos*
```
click "Crear proveedor" → modal alta, 5 inputs vacíos
  submit → valida presencia codigo/nombre + opcional no vacío tras trim → si falla inline sin fetch
  si ok → operacion={tipo:'alta',cargando:true} deshabilita "Crear"
    → crearProveedor({codigo:trim, nombre:trim, email:trimLower||undefined, telefono:trim||undefined, direccion:trim||undefined}) // vacío→no envía, null no se usa en alta
    → 4xx → mantiene modal + ErrorMessage validacion mensaje API
    → conexion/5xx → ErrorMessage conexion con Reintentar
    → 201 → cierra modal, banner "Proveedor creado correctamente" 3s, revalidar() → si revalidación falla mantiene éxito + error listado
```

**RF-3 Edición — mismo modal modo edicion** — *Propia por semántica `null`*
```
click "Editar" → modal edicion precarga nombre/email/telefono/direccion (null→""), codigo disabled
  usuario borra email y pulsa "Borrar" → campo marca null explícito
  usuario deja telefono sin tocar → campo ausente
  submit → valida: si todos ausentes/sin cambios → error local "Sin cambios" sin fetch; si algún opcional queda "" tras trim → error local
  si ok → operacion edicion cargando → editarProveedor(codigo, {nombre, email:null|valor|ausente, ...}) // sin codigo
    → 4xx mantiene modal + validacion; conexion → Reintentar; 200 → cierra + banner "Proveedor actualizado correctamente" + revalidar()
```

**RF-4 Baja — `ProveedorBajaDialog`** — *Idéntica a `006`*
```
click "Dar de baja" → diálogo "¿Dar de baja a <nombre> (<codigo>)? No se puede deshacer..."
  cancelar/ESC sin cargando → cierra
  confirmar → operacion baja cargando deshabilita Confirmar → bajaProveedor(codigo)
    → 4xx mantiene diálogo + validacion; conexion → Reintentar; 200 → cierra + banner + revalidar() → si 1→0 EmptyState
  navegar mientras cargando → petición no se cancela
```

> Todos deshabilitan botón `cargando` y usan `ErrorMessage`/`Loading`/`EmptyState` sin variantes — idéntica a `006`.

## 7. Decisiones técnicas justificadas (y alternativa descartada) — [Cubre RF-2..4, RNF-4]

1. **Modal en misma pantalla vs página separada** — *Idéntica a `006` decisión 1*
   - Elegida: modal + diálogo dentro de `Proveedores.jsx`.
   - Descartada: rutas `/proveedores/nuevo`.
   - Motivo: `spec.md:103` sin paginación, junior, preserva listado — idéntica.

2. **Modal casero Tailwind `role="dialog"` vs librería `react-modal`** — *Idéntica a `006` decisión 2*
   - Elegida: casero sin dependencia nueva, `AGENTS.md:27` y constitución §1.
   - Descartada: `react-modal`/`headlessui` — idéntica.

3. **Hook `useProveedores` vs estado en página** — *Idéntica a `006` decisión 3*
   - Elegida: hook encapsula `listar/crear/editar/baja` + revalidación.
   - Descartada: todo en `Proveedores.jsx` — idéntica.

4. **Banner éxito 3s vs toast global** — *Idéntica a `006` decisión 4*
   - Elegida: banner inline 3s sin `react-hot-toast`.
   - Descartada: toast — idéntica (fuera de alcance).

5. **`email`/`telefono`/`direccion` vacío `""`→bloqueo local vs enviar `""` a API** — *Propia (no existe en `006`)*
   - Elegida: `""`/`"   "` tras `trim` bloquea local sin `fetch` (error forma), `null` explícito vía botón "Borrar" envía `null`, ausente (no tocado) no se envía y conserva.
   - Descartada: enviar `""` y dejar que API lo rechace con 422.
   - Motivo: respeta `002` RF-1/RF-4 donde `""` es violación si se envía y `null` borra, pero evita llamada innecesaria y da feedback inmediato; `006` solo tenía `stock` vacío→ausencia, sin `null`.

6. **`stock_inicial` vacío→ausencia en `006` vs `email` vacío→bloqueo en `007`** — *Propia*
   - `006` elegía ausencia para `stock` vacío porque `0` y ausente ambos son válidos y `0` es valor por defecto; `007` elige bloqueo para `""` porque `""` nunca es válido para contacto y `null` es la forma de borrar, por lo que vacío sin intención explícita debe bloquearse.

## 8. Estrategia de tests — [Cubre RF-1..5, RNF-1..6, constitución §4] — *Análoga a 006 §8, extendida con semántica `null`*

Stack `Vitest` + `Testing Library` + `user-event` + `jsdom`, `fetch` mockeado vía `client.js`.

**`src/api/proveedores.js` — unidad (análoga a `productos.js` en `006`):**
- RF-1: `listarProveedores` 200 con 5 campos y `null`→"—" mapeado en tabla, `[]`→`EmptyState`, 401→validacion, 500→conexion.
- RF-2: `crearProveedor` `POST` con `codigo` sin `trim` (backend normaliza), `email`/`telefono`/`direccion` omitidos si `undefined`/`null` (ausencia), `409` duplicado incluye inactivo, `422` `email` sin `@`/`telefono` 6 dígitos, `500`→conexion.
- RF-3: `editarProveedor` `PATCH` con `codigo` normalizado, solo `nombre`/`email`/`telefono`/`direccion` (sin `codigo`), `null` borra, ausente conserva, `""` nunca se envía (bloqueo local), `404`/`400 inmutable`→validacion, `422` payload vacío→validacion (pero frontend ya bloquea).
- RF-4: `bajaProveedor` `DELETE`, `400 ya inactivo`→validacion, permite con movimientos previos (no valida `003` aquí).
- `grep -r "fetch(" src/components` vacío — idéntica.

**`Proveedores.jsx` — integración (análoga a `Productos.jsx` en `006`):**
- RF-1: monta→`Loading` luego `ProveedorTabla` 5 cols con "—" para `null` o `EmptyState`/`ErrorMessage` con Reintentar.
- RF-2: click "Crear proveedor" abre modal 5 campos, validación requerido bloquea `fetch`, submit `email`/`telefono` vacíos no llama, `email` con `"   "` bloquea, `POST` 201 cierra+revalida+banner, `409` mantiene modal, botón deshabilitado `cargando`.
- RF-3: click "Editar" precarga `null`→`""`, `codigo` disabled, `telefono` borrado vía botón "Borrar" envía `null`, campo no tocado no se envía, `""` tras trim bloquea, `PATCH` sin `codigo`, `404` por carrera mantiene modal.
- RF-4: click "Dar de baja" diálogo, cancelar/ESC cierra, Confirmar deshabilita, `DELETE` 200→cierra+revalida y si `1→0` `EmptyState`, `400` mantiene diálogo.
- RF-5: `localStorage` nunca usado, `revalidar` siempre `GET` tras mutación, `401` como validacion, múltiples clics → una sola petición.
- Casos límite propios: `__`/`--`/`*`/`ñ`/2/21, `email` `TEST@EXAMPLE.COM`→200, `telefono` `+34 600` 7-15 dígitos, `direccion` 5/200, `null` vs `""` vs ausente.

**`ProveedorTabla.jsx`, `ProveedorFormModal.jsx`, `ProveedorBajaDialog.jsx` — unidad (análogos a `006`):**
- Tabla 5 cols `codigo/nombre/email/telefono/direccion` sin `estado`, con "—" para `null`; modal 5 campos `label htmlFor`, `role="dialog"`, `codigo` disabled en edición, botón "Borrar" por campo opcional; diálogo texto confirmación.

> Criterio `spec.md:103`: `npm run test` verde, `npm run lint` sin errores, `grep -r "fetch(" src/components|hooks` vacío, español.

## 9. Cobertura de RFs — trazabilidad

| Parte del plan | RF cubierto | Evidencia verificable | Reutilizado de `006` |
|---|---|---|---|
| `ProveedorTabla.jsx` + `Proveedores.jsx` con `Loading`/`EmptyState`/`ErrorMessage` | RF-1 | tabla 5 cols con "—" para `null`, sin filtros/paginación | Sí (análoga) |
| `ProveedorFormModal.jsx` modo alta + `useProveedores.crear` | RF-2 | modal 5 campos, `""` bloquea, `null`/ausente no se envía, 4xx sin Reintentar, revalida | Sí (adaptada) |
| `ProveedorFormModal.jsx` modo edición + `useProveedores.editar` | RF-3 | `codigo` solo lectura, `null` borra con botón Borrar, ausente conserva, `""` bloquea, payload vacío bloquea | Parcial (propia semántica `null`) |
| `ProveedorBajaDialog.jsx` + `useProveedores.baja` | RF-4 | diálogo confirmación, `DELETE` aunque tenga movimientos, revalida y `EmptyState` 1→0 | Sí (idéntica) |
| `useProveedores` + `client.js` tipado + deshabilita | RF-5 | `validacion` sin Reintentar vs `conexion` con Reintentar, `localStorage` vacío, `401` | Sí (idéntica) |
| `a11y` labels, `role=dialog/alert`, `focus-visible:ring` | RNF-5, RNF-6 | `label htmlFor`, `lang="es"` | Sí |
| `api/proveedores.js` sin `fetch` en componentes | Constitución §3, §5 | `grep` vacío | Sí |

## 10. Fuera de alcance del plan (confirmado)

No se diseña búsqueda/filtros, paginación, ordenamiento, detalle inactivos, stock/movimientos, `codigo`/`estado` edit, reactivación, borrado físico, compras/facturas, i18n, tema oscuro, toasts, responsive — tal como `spec.md:92-101`.

## 11. Dudas abiertas

Ninguna bloqueante. No hay `[NECESITA ACLARACIÓN]`; reactivación (`002` duda) se evaluará en spec futura si se requiere.
