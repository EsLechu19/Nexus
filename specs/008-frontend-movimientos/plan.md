# Plan 008 — Frontend Movimientos de Inventario (Alta y Historial)

## 1. Alineación con constitución y AGENTS — [Cubre todos RF]

- Respeta `frontend/docs/constitution.md:3` stack mínimo (React 18 + Vite + Tailwind + fetch) — sin estado global para RF-1..4, idéntica a `006/plan.md:1` y `007/plan.md:1`.
- Respeta `frontend/docs/constitution.md:5` API aislada — todo HTTP en `src/api/movimientos.js` vía `src/api/client.js` de `005`; ningún `.jsx` hace `fetch` — RF-1..4, idéntica a `006`/`007`.
- Respeta `frontend/docs/constitution.md:7` estado servidor no cacheado — historial revalidado tras alta de entrada/salida, sin `localStorage` — RF-1, RF-4, idéntica a `006`/`007`.
- Respeta `frontend/docs/constitution.md:8` idioma español — mensajes genéricos de `005` + 4xx de `003` ya en español — RF-4, idéntica a `006`/`007`.
- Respeta `frontend/AGENTS.md:20` centralización `src/api/movimientos.js` y `AGENTS.md:28` validación solo forma — RF-2, RF-3, idéntica a `006`/`007`.
- Reutiliza `specs/005-frontend-base/plan.md:3-4,6` cliente `request` tipado (`validacion` vs `conexion`) y `Loading`/`ErrorMessage`/`EmptyState` — RF-1, RF-4, idéntica a `006`/`007`.
- Reutiliza patrón `specs/006-frontend-productos/plan.md:2-7` (listado + modal + hook + banner 3s) y `007/plan.md:2-7` (selects activos, semántica `null` no aplica aquí) — RF-1..4, adaptado a 7 columnas y doble `<select>`.
- Contratos exactos `specs/003-movimientos-inventario/plan.md:3` (endpoints `/api/v1/movimientos/entradas|/salidas`, `/api/v1/movimientos` historial, códigos 201/200/400/404/422, normalización `codigo`/`cantidad`/`motivo`, `proveedor` `null` para salidas) — RF-1..4, **propia** de este spec (movimientos).

## 2. Estructura de componentes dentro de `frontend/src/` — [Cubre RF-1..4]

```
frontend/src/
├── api/
│   ├── client.js                 # existente 005 — RF-3, RF-4
│   ├── productos.js              # existente 006 — usado para <select> productos — RF-2, RF-3
│   ├── proveedores.js            # existente 007 — usado para <select> proveedores — RF-2
│   └── movimientos.js            # nuevo — RF-1..4 — ver §3 (análoga a productos.js/proveedores.js, propia)
├── pages/
│   ├── Productos.jsx             # existente 006
│   ├── Proveedores.jsx           # existente 007
│   ├── Movimientos.jsx           # nuevo — RF-1..4 — orquesta historial, modal, revalidación (análoga a Productos.jsx/Proveedores.jsx, propia)
│   ├── PlaceholderPage.jsx       # existente 005
│   └── NotFoundPage.jsx          # existente 005
├── components/
│   ├── MovimientosHistorial.jsx  # nuevo — RF-1 — tabla 7 cols (fecha|producto|proveedor|tipo|cantidad|motivo|id), "—" para null (propia, análoga a ProductoTabla/ProveedorTabla pero 7 cols)
│   ├── MovimientoFormModal.jsx   # nuevo — RF-2, RF-3 — modal con selector Entrada|Salida + 4 campos condicionados (propia, análoga a ProductoFormModal/ProveedorFormModal con selector de tipo y doble <select>)
│   └── (reutilizados tal cual 005/006/007) Loading.jsx, ErrorMessage.jsx, EmptyState.jsx, ConfigErrorBanner.jsx — RF-1, RF-4
├── hooks/
│   ├── useProductos.js           # existente 006
│   ├── useProveedores.js         # existente 007
│   └── useMovimientos.js         # nuevo — RF-1, RF-4 — ver §4 (análoga a useProductos/useProveedores, propia)
└── App.jsx                       # existente — añadir ruta /movimientos → Movimientos.jsx — RF-1 (idéntica a 006/007)
```

Responsabilidad — **qué se reutiliza tal cual de `005`/`006`/`007` vs qué es propio:**
- **Reutilizado tal cual (sin tocar):** `Loading.jsx`, `ErrorMessage.jsx`, `EmptyState.jsx`, `ConfigErrorBanner.jsx`, `AppLayout.jsx`/`NavLinkItem.jsx`, `client.js`, patrón `useProductos/useProveedores` → `useMovimientos` (misma forma, distinto recurso), `App.jsx` con `BrowserRouter` future flags.
- **Propio (análogo a `006`/`007` pero con 7 cols y doble select):** `Movimientos.jsx` (análoga a `Productos.jsx`/`Proveedores.jsx` pero con historial + modal de alta condicionado), `MovimientosHistorial.jsx` (análoga a `ProductoTabla` 4 cols y `ProveedorTabla` 5 cols pero 7 cols y `fecha` ISO sin formateo), `MovimientoFormModal.jsx` (análoga a `ProveedorFormModal` 5 campos pero con `tabs Entrada|Salida` + `<select>` producto/proveedor), `src/api/movimientos.js` y `src/hooks/useMovimientos.js` (análogos a `productos.js`/`proveedores.js` pero con `tipo` y `cantidad`).

> Verificación constitución §3: `grep -r "fetch(" src/components src/pages src/hooks` vacío; solo `src/api/` contiene `fetch` — idéntica a `006`/`007`.

## 3. Consumo de endpoints vía cliente centralizado 005 — [Cubre RF-1..4] — *Propia (análoga a 006 §3 y 007 §3)*

`src/api/movimientos.js` importa `request` de `src/api/client.js` (valida `VITE_API_URL`, `AbortController` 10s, headers JSON, tipa `validacion` vs `conexion`). Misma forma que `src/api/productos.js`/`proveedores.js`, distinta ruta y payload con `proveedor` opcional según tipo. Los listados para `<select>` se obtienen vía `src/api/productos.js: listarProductos()` y `src/api/proveedores.js: listarProveedores()` ya existentes (no se duplica lógica).

```js
// src/api/movimientos.js — forma (análoga a productos.js/proveedores.js)
export function listarMovimientos() // GET /api/v1/movimientos → RF-1 (sin filtros, historial completo)
export function crearEntrada({ producto, proveedor, cantidad, motivo }) // POST /api/v1/movimientos/entradas → RF-2
export function crearSalida({ producto, cantidad, motivo }) // POST /api/v1/movimientos/salidas → RF-3
```

Los `<select>` usan funciones ya existentes (no nuevas):
```js
// para poblar selects (reutilizado 006/007)
import { listarProductos } from './productos.js'   // GET /api/v1/productos → RF-2, RF-3
import { listarProveedores } from './proveedores.js' // GET /api/v1/proveedores → RF-2
```

Ejemplo por operación (contrato `003/plan.md:3`):

**RF-1 GET historial — `listarMovimientos()`**
- Request: `GET /api/v1/movimientos` (`request('/api/v1/movimientos')`)
- Response 200: `[{"id":16,"producto_codigo":"PROD-003","proveedor_codigo":null,"tipo":"salida","cantidad":8,"motivo":"Venta mostrador","fecha":"2026-09-08T12:00:00Z"}, {"id":15,"producto_codigo":"PROD-003","proveedor_codigo":"PROV-002","tipo":"entrada","cantidad":10,"motivo":"Compra semanal","fecha":"2026-09-08T11:00:00Z"}, {"id":1,"producto_codigo":"PROD-003","proveedor_codigo":null,"tipo":"entrada_inicial","cantidad":5,"motivo":null,"fecha":"2026-09-07T10:00:00Z"}]` → mapeo directo a 7 cols, `null`→"—", orden `fecha desc + id desc` garantizado por backend, frontend no reordena
- Response 200 vacío: `[]` → `EmptyState`
- Error 4xx → `validacion` sin Reintentar; 5xx/red → `conexion` con Reintentar

**RF-1 GET selects — `listarProductos()` / `listarProveedores()` (reutilizado)**
- Request: `GET /api/v1/productos` y `GET /api/v1/proveedores` (`request('/api/v1/productos')` / `request('/api/v1/proveedores')`)
- Response 200: `[{"codigo":"PROD-001","nombre":"Juego A"}, {"codigo":"PROV-002","nombre":"Proveedor Central"}]` → opciones `${codigo} — ${nombre}`, `disabled` con `Cargando...` mientras cargan, `[]` → bloquea "Crear" con mensaje puntual
- Error 5xx/red → `ErrorMessage conexion` con Reintentar que reejecuta solo la carga del `<select>`; 4xx/401 → `ErrorMessage validacion` sin Reintentar, bloqueado hasta cerrar/reabrir modal

**RF-2 POST entrada — `crearEntrada({producto, proveedor, cantidad, motivo})`**
- Request: `POST /api/v1/movimientos/entradas` body `{"producto_codigo":"  prod-003 ","proveedor_codigo":" prov-002 ","cantidad":10,"motivo":"Compra semanal"}` → normalización `trim+mayúsculas` y `motivo trim` lo hace backend
- Body sin motivo: `{"producto_codigo":"PROD-003","proveedor_codigo":"PROV-002","cantidad":10}` (motivo `null/ausente` omitido)
- Response 201: `{"id":15,"producto_codigo":"PROD-003","proveedor_codigo":"PROV-002","tipo":"entrada","cantidad":10,"motivo":"Compra semanal","fecha":"2026-09-08T11:00:00Z","stock_actual":15}`
- Error 404 producto/proveedor no existe / 400 inactivo / 400 stock no aplica / 422 `cantidad`/`motivo` → `validacion` sin Reintentar; 5xx/red → `conexion` con Reintentar

**RF-3 POST salida — `crearSalida({producto, cantidad, motivo})`**
- Request: `POST /api/v1/movimientos/salidas` body `{"producto_codigo":"PROD-003","cantidad":8,"motivo":"Venta mostrador"}` (nunca incluye `proveedor_codigo`, aunque hubiera sido seleccionado en `Entrada` se omite)
- Body sin motivo: `{"producto_codigo":"PROD-003","cantidad":8}`
- Response 201: `{"id":16,"producto_codigo":"PROD-003","proveedor_codigo":null,"tipo":"salida","cantidad":8,"motivo":"Venta mostrador","fecha":"2026-09-08T12:00:00Z","stock_actual":7}`
- Error 400 producto inactivo / 400 stock insuficiente (`cantidad > stock_actual`) / 404 no existe / 422 → `validacion`; 5xx/red → `conexion`
- Si se envía `proveedor_codigo` en salida → `422` (no permitido), pero frontend nunca lo envía al ocultar el campo

> Todas usan `VITE_API_URL` vía `client.js` sin hardcodeo — idéntica a `006`/`007`.

## 4. Diseño del selector de tipo (Entrada/Salida) y campos condicionados — [Cubre RF-2, RF-3] — *Propio (no existe en 006/007)*

`MovimientoFormModal.jsx` presenta `tabs/radio` `Entrada | Salida` (`Entrada` preseleccionada) accesible por teclado (`role="tablist"` o `radiogroup` con `roving tabindex`, `aria-selected`/`aria-checked`).

- **Entrada** muestra: `producto <select>` requerido + `proveedor <select>` requerido + `cantidad` requerido + `motivo` opcional.
- **Salida** muestra: `producto <select>` requerido + `cantidad` requerido + `motivo` opcional (sin `proveedor`).

**Manejo de estado al cambiar de tipo (dentro del modal, memoria efímera del modal, no `localStorage`):**
- Al cambiar `Entrada → Salida`: se **conservan** `producto`, `cantidad`, `motivo` ya escritos y se **limpian** errores de validación previos asociados a `proveedor`; `proveedor` se **oculta y limpia** (`value=""`) para evitar envío erróneo; ningún otro campo se resetea.
- Al cambiar `Salida → Entrada`: `proveedor` queda **vacío** (`""`) y requiere nueva selección, conservando `producto/cantidad/motivo` y limpiando errores previos.
- Al abrir el modal: `tipo` resetea a `Entrada`, todos los campos vacíos y errores limpios; al cerrar y reabrir, se reintentan cargas de `<select>` si habían fallado.

> RF-2, RF-3, RNF-4 — **Propio** de este spec (selector condicional y conservación parcial no existe en `006`/`007`).

## 5. Modelo de estado local — [Cubre RF-1..4, RNF-3] — *Idéntica a 006 §4 y 007 §4 en historial, propia en doble select*

`Movimientos.jsx` + `useMovimientos.js` viven solo en memoria, revalidan tras alta, sin `localStorage` — idéntica a `Productos.jsx`/`useProductos.js`, distinta entidad y con doble carga para `<select>`.

```js
// forma del estado en Movimientos.jsx (análoga a Productos.jsx/Proveedores.jsx, propia con doble select)
{
  movimientos: [],           // Array<{id,producto_codigo,proveedor_codigo,tipo,cantidad,motivo,fecha}> — RF-1
  productos: [],             // Array<{codigo,nombre}> para <select> producto — RF-2, RF-3
  proveedores: [],           // Array<{codigo,nombre}> para <select> proveedor — RF-2
  tipoSeleccionado: 'entrada'|'salida', // 'entrada' por defecto — RF-2, RF-3
  cargandoHistorial: false,  // boolean — RF-1
  cargandoSelects: false,    // boolean — RF-2 (producto/proveedor)
  cargandoAlta: false,       // boolean — RF-2, RF-3 (deshabilita "Crear")
  errorHistorial: null,      // {tipo,mensaje,reintentable}|null — RF-1
  errorSelects: null,        // {tipo,mensaje}|null — RF-2 (bloquea formulario)
  errorAlta: null,           // {tipo,mensaje}|null — RF-2, RF-3 (dentro del modal)
  modal: { abierto: false }, // RF-2, RF-3
  mensajeExito: null         // "Movimiento registrado correctamente" — RF-2, RF-3, 3s
}
```

`useMovimientos.js` expone — análoga a `useProductos`/`useProveedores`:
- `movimientos, cargandoHistorial, errorHistorial, revalidar()` — RF-1 (`GET` sin filtros, orden backend)
- `productos, proveedores, cargandoSelects, errorSelects, cargarSelects()` — RF-2 (dos `GET` paralelos solo activos ordenados)
- `crearEntrada(payload)` → `POST /entradas` → `revalidar()` — RF-2
- `crearSalida(payload)` → `POST /salidas` → `revalidar()` — RF-3
- Nunca cachea `localStorage` (constitución §5) — idéntica.

> RF-1, RF-2, RF-3, RF-4, RNF-3 — **Reutilizado** patrón de `006`/`007`, **propio** doble `productos/proveedores` para `<select>`.

## 6. Contrato de validación de formulario — [Cubre RF-2, RF-3, RNF-1] — *Propia (análoga a 007 §5 pero con cantidad)*

**Frontend valida solo forma/UX, fuente de verdad es API (`AGENTS.md:28`) — idéntica filosofía a `006`/`007`, propia para `cantidad`/`motivo`:**

| Campo | Regla forma frontend (sin API) | Mensaje local | Regla negocio backend (API `003`) | Mensaje API |
|-------|-------------------------------|---------------|-----------------------------------|-------------|
| `producto` | requerido (`<select>` no vacío) | "Campo requerido" | `3-20` `^[A-Z0-9_-]{3,20}$` tras `trim+mayúsculas`, existe y `activo` | `404` no existe / `400` inactivo |
| `proveedor` | requerido solo para `Entrada` (`<select>` no vacío) | "Campo requerido" | mismo formato que `producto`, existe y `activo` solo para `entrada` | `404`/`400` |
| `cantidad` | requerida tras `trim`, debe coincidir con `/^-?\d+$/` y `Number.isInteger(Number(v)) && Number(v) > 0` (`" 5 "`→`5` válido, `"001"`→`1` válido) | "Campo requerido" si vacío, "Debe ser un número entero mayor a 0" si `1.5`/`-1`/`0`/`abc`/`1.0`/`1,5` | `1..1_000_000` entero, `>1_000_000`→`422` | `422` |
| `motivo` | si informado y no es `null`, no debe quedar vacío tras `trim` (`""`/`"   "` → bloquea) | "No puede quedar vacío" | `trim` `2-200` sin `\n`/`\r`, `null`/ausente→`NULL`, `""`/`1`/`201`/`\n`→`422`, conteo `String.length` | `422` |

- Frontend nunca valida `producto`/`proveedor` formato exacto, unicidad, ni `trim+mayúsculas` más allá de `required` del `<select>`; nunca valida `cantidad` límite `1_000_000` ni `motivo` `2-200`/`\n`; esos `422` se muestran tal cual vienen de `003` — **idéntica a `006`/`007`**.
- **Propia vs `006`/`007`:** en `006` `stock_inicial` vacío→ausencia, en `007` `email` `""`→bloqueo con `null`/`ausente`/`""` triple semántica; aquí `cantidad` `""`→`Campo requerido` y `" 1.0 "`→error entero `>0` local, `motivo` `""`→bloqueo local, `null`/ausente→omitido (no se envía).
- Al cambiar `Entrada↔Salida`, errores previos se limpian — **propia** (no existe en `006`/`007`).

**Manejo de listados vacíos o con error para `<select>` (RF-2):**
- `[]` → botón "Crear" `disabled` + mensaje puntual `"No hay productos activos disponibles. Crea un producto primero."` o `"No hay proveedores activos..."` diferenciado por tipo (`Entrada` bloquea si falta cualquiera, `Salida` solo si falta `producto`).
- `4xx` (incluido `401`) → `ErrorMessage validacion` sin `Reintentar` dentro del modal, formulario bloqueado; cerrar y reabrir reintenta la carga.
- `5xx`/red → `ErrorMessage conexion` con `Reintentar` dentro del modal que reejecuta solo el `GET` del `<select>` fallido.

## 7. Flujo de alta y revalidación (pseudocódigo) — [Cubre RF-1..4, RNF-2] — *Idéntica a 006 §6 y 007 §6 en revalidación, propia en doble select*

**RF-1 Historial — `Movimientos.jsx` + `useMovimientos.js`** — *Idéntica a `006`/`007` con 7 cols*
```
al montar: cargandoHistorial=true → <Loading />
  GET /movimientos (sin filtros) → [] → <EmptyState> "Sin datos disponibles"
                → 4xx → <ErrorMessage validacion> sin Reintentar
                → conexion/5xx → <ErrorMessage conexion onReintentar=revalidar />
  éxito → <MovimientosHistorial> 7 cols (fecha|producto|proveedor|tipo|cantidad|motivo|id con "—" para null)
  App.jsx: /movimientos → Movimientos.jsx bajo AppLayout (idéntica a 006/007)
```

**RF-2 Alta Entrada — `MovimientoFormModal` modo entrada** — *Propia por doble <select>*
```
click "Crear movimiento" → modal con tipo=Entrada preseleccionado, selects disabled con "Cargando..." → al resolver:
  si productos/proveedores [] → mensaje puntual + "Crear" disabled
  si error select 4xx → ErrorMessage validacion sin Reintentar (reabrir reintenta) + bloqueado
  si error 5xx → ErrorMessage conexion con Reintentar (reejecuta solo ese GET) + bloqueado
  else → selects habilitados con opciones "${codigo} — ${nombre}"
usuario completa y submit → valida presencia producto/proveedor + cantidad>0 entero + motivo no vacío tras trim → si falla inline sin fetch, limpia errores previos al cambiar tipo
si ok → operacion={cargandoAlta:true} deshabilita "Crear"
  → crearEntrada({producto_codigo:trim+mayúsculas solo extremos, proveedor_codigo:trim+mayúsculas, cantidad:Number(trim), motivo:trim||undefined}) // motivo vacío→omitido
  → 4xx → mantiene modal + ErrorMessage validacion mensaje API (ej. 404 inactivo, 422 cantidad>1M)
  → conexion/5xx → ErrorMessage conexion con Reintentar (re-ejecuta solo POST entrada)
  → 201 → cierra modal, banner "Movimiento registrado correctamente" 3s role="status" (reinicia timer si existe), revalidar() GET historial → si revalidación falla mantiene éxito + ErrorMessage listado debajo del banner
```

**RF-3 Alta Salida — mismo modal modo salida** — *Propia por ocultar proveedor*
```
click tab "Salida" → oculta proveedor, conserva producto/cantidad/motivo, limpia errores de proveedor y oculta/limpia valor proveedor
submit → valida solo producto/cantidad + motivo no vacío
si ok → operacion salida cargando → crearSalida({producto_codigo,cantidad,motivo}) // sin proveedor_codigo
  → 4xx mantiene modal + validacion (ej. 400 stock insuficiente "Stock insuficiente")
  → conexion → Reintentar; 201 → cierra + banner + revalidar() (misma coexistencia si falla)
```

**RF-4 Revalidación uniforme** — *Idéntica a `006`/`007`*
```
cualquier alta con éxito → revalidar() GET /movimientos (completo, sin filtros) sin localStorage; si falla 401→validacion sin Reintentar además del éxito, si 5xx→conexion con Reintentar; banner y error coexisten (banner arriba, ErrorMessage debajo)
durante alta en curso → ESC y navegación se ignoran, petición no se cancela (AbortController no aborta alta en curso), al volver se ve resultado tras revalidar
botones deshabilitados mientras cargando evitan duplicados locales; concurrencia distribuida resuelta vía 4xx específico
```

> Todos usan `Loading`/`EmptyState`/`ErrorMessage` sin variantes y `role="status"` vs `role="alert"` — idéntica a `006`/`007`.

## 8. Decisiones técnicas justificadas (y alternativa descartada) — [Cubre RF-1..4, RNF-4]

1. **Modal en misma pantalla vs página separada `/movimientos/nuevo`** — *Idéntica a `006` decisión 1 y `007` decisión 1*
   - Elegida: modal con selector `Entrada|Salida` dentro de `Movimientos.jsx`.
   - Descartada: ruta separada para alta.
   - Motivo: `spec.md:94` sin paginación, junior, preserva historial visible — idéntica.

2. **Modal casero Tailwind `role="dialog"` vs librería `react-modal`** — *Idéntica a `006` decisión 2 y `007` decisión 2*
   - Elegida: casero sin dependencia nueva, `AGENTS.md:27` y constitución §1.
   - Descartada: `react-modal`/`headlessui` — idéntica.

3. **Hook `useMovimientos` vs estado en página** — *Idéntica a `006` decisión 3 y `007` decisión 3*
   - Elegida: hook encapsula `listado historial` + `listados selects` + `revalidación`.
   - Descartada: todo en `Movimientos.jsx` — idéntica (separa presentación de lógica).

4. **Banner éxito 3s vs toast global** — *Idéntica a `006` decisión 4 y `007` decisión 4*
   - Elegida: banner inline `role="status"` 3s sobre historial.
   - Descartada: `react-hot-toast` — idéntica (fuera de alcance).

5. **Tabs `Entrada|Salida` que condicionan campos vs dos modales separados `EntradaModal`/`SalidaModal`** — *Propia (no existe en 006/007)*
   - Elegida: un `MovimientoFormModal.jsx` con `tipo` state y render condicional del `<select>` proveedor.
   - Descartada: dos componentes modales separados o dos páginas.
   - Motivo: evita duplicar `producto/cantidad/motivo` y lógica de validación/bloqueo; conserva valores al cambiar de tipo (salvo `proveedor`) y simplifica `handleCrear` con `if (tipo==='entrada') crearEntrada else crearSalida`; dos modales duplicarían 80% de código y obligarían a sincronizar `selects`.

6. **Doble carga de listados `productos`+`proveedores` en paralelo para `<select>` vs carga lazy al abrir modal** — *Propia (006/007 solo cargan un listado)*
   - Elegida: `useMovimientos` expone `cargarSelects()` que hace `Promise.all([listarProductos(), listarProveedores()])` al montar `Movimientos.jsx` y también al abrir el modal si falló; `MovimientoFormModal` recibe ya `productos/proveedores` por props.
   - Descartada: cargar cada `<select>` dentro del modal con `useEffect` separado.
   - Motivo: centraliza `cargandoSelects`/`errorSelects` en el hook (misma forma que `cargandoHistorial`), reutiliza `productos.js`/`proveedores.js` sin duplicar `fetch`, y permite bloquear "Crear" si `[]` sin esperar a abrir modal; carga lazy duplicaría lógica y violaría `AGENTS.md:20` centralización.

7. **`cantidad` `""` → "Campo requerido" y `"1.0"` → "Debe ser un número entero mayor a 0" vs enviar `""` a API** — *Propia (006 tenía `stock` vacío→ausencia, 007 tenía `""`→bloqueo con `null`)*
   - Elegida: `""`/`"   "` tras `trim` bloquea local sin `fetch` para `cantidad` y `motivo`, `"1.0"`/`"-1"`/`"0"` bloquea local como entero `>0` inválido.
   - Descartada: enviar `""` y dejar que API lo rechace con `422`.
   - Motivo: respeta `003` donde `cantidad` `0`/`1.5` y `motivo` `""` son `422`, pero evita llamada innecesaria y da feedback inmediato; `1_000_000` límite se deja al backend para no duplicar validación.

8. **`proveedor` oculto en `Salida` vs enviar `proveedor:null`** — *Propia*
   - Elegida: `proveedor` no se renderiza y se omite del payload en `Salida` (aunque existía valor en `Entrada`, se limpia al ocultar).
   - Descartada: enviar `proveedor:null` en `Salida`.
   - Motivo: `003` especifica que `salida` con `proveedor` debe ser ignorado o `422`; no enviarlo evita ambigüedad y respeta contrato `003/plan.md:3` donde `proveedor_codigo` solo existe para `entrada`.

## 9. Estrategia de tests — [Cubre RF-1..4, RNF-1..6, constitución §4] — *Análoga a 006 §8 y 007 §8, extendida con doble select y tipos*

Stack `Vitest` + `Testing Library` + `user-event` + `jsdom`, `fetch` mockeado vía `client.js` (sin tocar red).

**`src/api/movimientos.js` — unidad (análoga a `productos.js`/`proveedores.js` en 006/007):**
- RF-1: `listarMovimientos` `200` con 7 campos y `null`→"—" en historial (pero mapeo es en componente), `[]`→`EmptyState`, `401→validacion`, `500→conexion`, orden `fecha desc` sin reordenar.
- RF-2: `crearEntrada` `POST /entradas` con `producto`/`proveedor` sin `trim` (backend normaliza), `cantidad` `1`/`1_000_000` límite, `motivo` omitido vs `"   "`→`422`, `404` producto/proveedor no existe, `400` inactivo, `422` `cantidad>1M`, `500→conexion`.
- RF-3: `crearSalida` `POST /salidas` sin `proveedor`, `400` stock insuficiente, `404`, `422`, nunca envía `proveedor` aunque se informe.
- `grep -r "fetch(" src/components|hooks|pages` vacío — idéntica.

**`Movimientos.jsx` — integración (análoga a `Productos.jsx`/`Proveedores.jsx` en 006/007, propia por doble select y tipos):**
- RF-1: monta→`Loading` luego `MovimientosHistorial` 7 cols con "—" para `null` o `EmptyState`/`ErrorMessage` con Reintentar; `App.jsx` `/movimientos` bajo `AppLayout`.
- RF-2: click "Crear movimiento" abre modal `Entrada` preseleccionada con dos `<select>` (`Cargando...` → opciones), `[]` bloquea `Crear` con mensaje puntual, `5xx` en `<select>` muestra `ErrorMessage` con Reintentar; valida `producto/proveedor/cantidad` requerido bloquea `fetch`, `cantidad` `"1.0"`→"Debe ser entero mayor a 0", `POST` `201` cierra+revalida+banner, `409`/`422` mantiene modal, botón `Crear` disabled `cargando`, cambio `Entrada→Salida` conserva `producto/cantidad/motivo` y limpia `proveedor`/errores.
- RF-3: tab `Salida` oculta `proveedor`, `proveedor` previo no se envía, `cantidad` `0`/`-1` bloquea, `POST` `201` sin `proveedor`, `400` stock insuficiente mantiene modal, `5xx` con Reintentar.
- RF-4: `localStorage` nunca usado, `revalidar` siempre `GET` completo tras alta, `401` como `validacion` sin Reintentar, múltiples clics → una sola petición, `ESC` ignorado durante `cargando`.
- Casos límite propios: `cantidad` `"001"`→`1` válido, `" 5 "` válido, `motivo` `" a "`→`"a"` enviado y `422` del backend, `producto`/`proveedor` `inactivo` entre carga y envío → `400` específico, `historial` `401` sin `Reintentar` con `Crear` aún habilitado.

**`MovimientosHistorial.jsx`, `MovimientoFormModal.jsx` — unidad (análogos a 006/007):**
- Historial 7 cols `fecha|producto|proveedor|tipo|cantidad|motivo|id` sin filtros, con "—" para `null`, `fecha` ISO sin formateo; modal `role="dialog"` `aria-modal` con `tabs` `Entrada|Salida`, 4 campos condicionados, `label htmlFor`, `proveedor` `disabled` con `Cargando...` y mensaje vacío, `Reintentar` para carga de selects.

> Criterio `spec.md:94`: `npm run test` verde, `npm run lint` sin errores, `grep -r "fetch(" src/components|hooks|pages` vacío, español, `lang="es"`.

## 10. Cobertura de RFs — trazabilidad

| Parte del plan | RF cubierto | Evidencia verificable | Reutilizado de `006`/`007` |
|---|---|---|---|
| `MovimientosHistorial.jsx` + `Movimientos.jsx` con `Loading`/`EmptyState`/`ErrorMessage` | RF-1 | tabla 7 cols con "—" para `null`, sin filtros/paginación, orden `fecha desc` | Sí (análoga 4/5 cols) |
| `MovimientoFormModal.jsx` modo `Entrada` + `useMovimientos.crearEntrada` + `listarProductos`/`listarProveedores` | RF-2 | modal con 2 `<select>` activos ordenados, `cantidad>0` entero, `motivo` no vacío, `[]` bloquea, `4xx` sin Reintentar, revalida | Parcial (propia doble select) |
| `MovimientoFormModal.jsx` modo `Salida` (oculta `proveedor`) + `useMovimientos.crearSalida` | RF-3 | `proveedor` no se renderiza ni se envía, conserva `producto/cantidad/motivo` al cambiar tipo, `400` stock insuficiente, `5xx` con Reintentar | Propia (selector tipo) |
| `useMovimientos` + `client.js` tipado + `Reintentar` select + deshabilita | RF-4 | `validacion` sin Reintentar vs `conexion` con Reintentar, `localStorage` vacío, `401` sin redirección, `cargandoAlta` disabled | Sí (idéntica) |
| `a11y` labels, `role=dialog/alert`, `focus-visible:ring`, `htmlFor` | RNF-5, RNF-6 | `label htmlFor`, `tabs` accesibles, `lang="es"` | Sí |
| `api/movimientos.js` sin `fetch` en componentes | Constitución §3, §5 | `grep` vacío | Sí |

## 11. Fuera de alcance del plan (confirmado)

No se diseña búsqueda/filtros UI, paginación, ordenamiento distinto a `fecha desc + id desc`, valorización/reservas/lotes, edición/borrado de movimientos, valorización económica, `stock_actual` en esta pantalla (para `009`), `stock_inicial`/`categoria` edit, reactivación, borrado físico, i18n, tema oscuro, toasts, responsive — tal como `spec.md:84-92`.

## 12. Dudas abiertas

Ninguna bloqueante. No hay `[NECESITA ACLARACIÓN]`; paginación, filtros avanzados y valorización se evaluarán en spec futura si se requieren; stock en `009`.
