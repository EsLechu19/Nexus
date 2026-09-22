# Plan 009 — Frontend Consulta de Stock (Solo Lectura con Alerta)

## 1. Alineación con constitución y AGENTS — [Cubre todos RF]

- Respeta `frontend/docs/constitution.md:3` stack mínimo (React 18 + Vite + Tailwind + fetch) — sin estado global para RF-1..2, idéntica a `006/plan.md:1` y `008/plan.md:1`.
- Respeta `frontend/docs/constitution.md:5` API aislada — todo HTTP en `src/api/stock.js` vía `src/api/client.js` de `005`; ningún `.jsx` hace `fetch` — RF-1..2, idéntica a `006`/`008`.
- Respeta `frontend/docs/constitution.md:7` estado servidor no cacheado — listado stock releído en cada acceso a `/stock`, sin `localStorage` — RF-1, RF-2, idéntica a `008`.
- Respeta `frontend/docs/constitution.md:8` idioma español — mensajes genéricos de `005` + 4xx de `004` ya en español — RF-2, idéntica a `006`.
- Respeta `frontend/AGENTS.md:20` centralización `src/api/stock.js` y `AGENTS.md:28` validación solo forma — RF-1, idéntica a `008`.
- Reutiliza `specs/005-frontend-base/plan.md:3-4,6` cliente `request` tipado (`validacion` vs `conexion`) y `Loading`/`ErrorMessage`/`EmptyState` — RF-2, idéntica a `008`.
- Reutiliza patrón `specs/006-frontend-productos/plan.md:2-7` (listado + hook + banner no aplica aquí) y `008/plan.md:2-7` (tabla 7 cols + hook con `Promise.all`) — RF-1..2, adaptado a 5 cols y solo lectura sin `Promise.all`.
- Contratos exactos `specs/004-consulta-stock/plan.md:3` (endpoint `GET /api/v1/stock` y `GET /api/v1/stock/{codigo}`, códigos 200/404/422, campo `alerta` boolean ya calculado, `stock_minimo` `0..1_000_000`, orden `codigo ASC`) — RF-1..2, **propia** de este spec (stock).

## 2. Estructura de componentes dentro de `frontend/src/` — [Cubre RF-1..2]

```
frontend/src/
├── api/
│   ├── client.js                 # existente 005 — RF-2
│   ├── productos.js              # existente 006 — no usado aquí, pero stock_minimo editable allí
│   ├── proveedores.js            # existente 007
│   ├── movimientos.js            # existente 008
│   └── stock.js                  # nuevo — RF-1..2 — ver §3 (análoga a productos.js, propia)
├── pages/
│   ├── Productos.jsx             # existente 006
│   ├── Proveedores.jsx           # existente 007
│   ├── Movimientos.jsx           # existente 008
│   ├── Stock.jsx                 # nuevo — RF-1..2 — orquesta listado stock y estados (análoga a Productos.jsx pero solo lectura, sin modal)
│   ├── PlaceholderPage.jsx       # existente 005
│   └── NotFoundPage.jsx          # existente 005
├── components/
│   ├── StockTabla.jsx            # nuevo — RF-1 — tabla 5 cols (codigo|nombre|stock_actual|stock_minimo|alerta) con badge y fila marcada (propia, análoga a ProductoTabla 4 cols pero con alerta)
│   └── (reutilizados tal cual 005/006/007/008) Loading.jsx, ErrorMessage.jsx, EmptyState.jsx, ConfigErrorBanner.jsx — RF-2
├── hooks/
│   ├── useProductos.js           # existente 006
│   ├── useProveedores.js         # existente 007
│   ├── useMovimientos.js         # existente 008
│   └── useStock.js               # nuevo — RF-1..2 — ver §6 (análoga a useProductos pero solo lectura, sin mutaciones)
└── App.jsx                       # existente — añadir ruta /stock → Stock.jsx — RF-1 (idéntica a 006/007/008)
```

Responsabilidad — **qué se reutiliza tal cual vs qué es propio:**
- **Reutilizado tal cual (sin tocar):** `Loading.jsx`, `ErrorMessage.jsx`, `EmptyState.jsx`, `ConfigErrorBanner.jsx`, `AppLayout.jsx`/`NavLinkItem.jsx`, `client.js`, `App.jsx` con `BrowserRouter` future flags.
- **Propio (análogo a `006`/`008` pero solo lectura):** `Stock.jsx` (análoga a `Productos.jsx`/`Movimientos.jsx` pero sin modal/banner de éxito, solo orquesta `useStock`), `StockTabla.jsx` (análoga a `MovimientosHistorial.jsx` 7 cols pero 5 cols con `alerta` badge + fila coloreada, y a `ProductoTabla` 4 cols), `src/api/stock.js` y `src/hooks/useStock.js` (análogos a `movimientos.js`/`useMovimientos` pero con solo `listarStock` y sin `Promise.all`).

> Verificación constitución §3: `grep -r "fetch(" src/components src/pages src/hooks` vacío; solo `src/api/` contiene `fetch` — idéntica a `008`.

## 3. Consumo de endpoint vía cliente centralizado 005 — [Cubre RF-1..2] — *Propia (análoga a 008 §3)*

`src/api/stock.js` importa `request` de `src/api/client.js` (valida `VITE_API_URL`, `AbortController` 10s, headers JSON, tipa `validacion` vs `conexion`). Misma forma que `src/api/productos.js`, distinta ruta y sin payload. No reutiliza `productos.js` para stock (stock tiene endpoint propio `004`).

```js
// src/api/stock.js — forma (análoga a movimientos.js)
export function listarStock() // GET /api/v1/stock → RF-1, RF-2 (listado global, sin filtros)
```

Ejemplo por operación (contrato `004/plan.md:3`):

**RF-1 GET stock global — `listarStock()`**
- Request: `GET /api/v1/stock` (`request('/api/v1/stock')`)
- Response 200: `[{"codigo":"PROD-001","nombre":"PlayStation 5 Slim","stock_actual":14,"stock_minimo":10,"alerta":false}, {"codigo":"PROD-002","nombre":"Zelda TOTK","stock_actual":0,"stock_minimo":5,"alerta":true}, {"codigo":"PROD-003","nombre":"Mayorista Norte","stock_actual":5,"stock_minimo":10,"alerta":true}]` → mapeo directo a 5 cols, `alerta` boolean ya calculado por backend (ej. `0<5 → true`, `14<10? false`), orden `codigo ASC` garantizado por backend, frontend no reordena. Campos extra del contrato (`stock_inicial`, `entradas`, `salidas`) vienen en el JSON pero se ignoran sin mostrarlos.
- Response 200 vacío: `[]` → `EmptyState` (también `null`/`204` tratado como `[]` en `Stock.jsx`, ver §8)
- Response 200 con `null`/`204` o todas filas corruptas → `EmptyState` (ver §5)
- Error 4xx (incl. `401`) → `validacion` sin Reintentar; `404` nunca en global (siempre `200` con `[]`); `5xx`/red → `conexion` con Reintentar
- Nota: `GET /api/v1/stock/{codigo}` (detalle) existe en `004` pero no se consume en este spec (fuera de alcance `spec.md:60`), no hay función `obtenerStockPorCodigo` en `stock.js` para MVP.

> Todas usan `VITE_API_URL` vía `client.js` sin hardcodeo — idéntica a `008`.

## 4. Diseño de la columna/badge de alerta y el resalte de fila — [Cubre RF-1] — *Propia (no existe en 006/007/008)*

`StockTabla.jsx` presenta 5 columnas `codigo|nombre|stock_actual|stock_minimo|alerta` (análoga a `ProductoTabla` 4 cols y `MovimientosHistorial` 7 cols, propia por `alerta`).

- **Columna `alerta` (siempre presente, nunca vacía):** muestra badge de texto `"Bajo stock"` cuando `alerta === true`, y `"—"` cuando `alerta === false`. No queda vacía ni muestra `true`/`false` crudo. `badge` es texto accesible (fuente de verdad para lector de pantalla), no solo color.
- **Resalte de fila (refuerzo, nunca solo color):** cuando `alerta === true`, la `<tr>` además de badge se marca con estado visual diferenciado (ej. Tailwind `bg-red-50` / borde) de forma consistente en toda la tabla. Cuando `alerta === false`, fila sin marca. **Nunca solo color sin badge**, por `RNF-6` accesibilidad — el badge es obligatorio.
- **Clases condicionales (ilustrativo, no código final):** `alerta ? "bg-red-50 text-red-800" : ""` en `<tr>` y `alerta ? "bg-red-100 text-red-700"` en badge `<span>`; `stock_actual`/`stock_minimo` sin clases especiales. Tailwind ya disponible por `005`, sin nueva dependencia.
- **Frontend NUNCA reimplementa fórmula:** no calcula `stock_minimo > 0 && stock_actual < stock_minimo`; solo lee `alerta` boolean tal cual. La fórmula se documenta en `RNF-1` solo para que los tests verifiquen que el backend la respeta (ej. `5<10 → true`).

> RF-1, `RNF-1`, `RNF-6` — **Propia** de este spec (alerta boolean + badge+fila no existe en `006`/`008` que usaba `—` para `null` pero sin alerta).

## 5. Regla de renderizado defensivo — [Cubre RF-1] — *Propia (no existe en 006/007/008)*

Antes de pintar, `StockTabla.jsx` valida cada fila recibida de `listarStock()`; si una fila es inválida se omite sin romper el resto (principio defensivo ya usado en `008` para `null→"—"` pero aquí se omite fila completa).

```js
// validación por fila antes de <tr> (ilustrativo)
function esFilaStockValida(f) {
  return typeof f.codigo === 'string' && f.codigo.trim() !== ''
      && typeof f.nombre === 'string' && f.nombre.trim() !== ''
      && Number.isInteger(f.stock_actual)
      && Number.isInteger(f.stock_minimo)
      && typeof f.alerta === 'boolean';
}
// en render: filasFiltradas = movimientos.filter(esFilaStockValida)
// si filasFiltradas.length === 0 pero original.length > 0 → mostrar EmptyState (equivalente a [])
```

- **Campos obligatorios para render:** `codigo` (string no vacío), `nombre` (string no vacío), `stock_actual` (integer), `stock_minimo` (integer), `alerta` (boolean). Si falta alguno, es `null`/`undefined`, o tipo incorrecto (`stock_actual` string/float, `alerta` string, `codigo` number), esa fila se **omite**.
- **Campos extra no contemplados:** `stock_inicial`, `entradas`, `salidas` u otros que `004` sí devuelve se **ignoran** sin validarlos ni mostrarlos (no rompen render).
- **Si todas las filas son corruptas:** lista filtrada `[]` → `Stock.jsx` muestra `EmptyState` (mismo que `[]` legítimo), ver §8.
- **Duplicados `codigo`:** se muestran ambas filas tal cual (key `codigo + índice`), sin deduplicar — idéntica a no deduplicar en `008`.

> RF-1, casos límite `spec.md:52` — **Propia** (defensa por fila no existe en `006`/`008` que solo mapeaba `null→"—"`).

## 6. Modelo de estado local — [Cubre RF-1..2, RNF-3] — *Idéntica a 006 §4 pero solo lectura*

`Stock.jsx` + `useStock.js` viven solo en memoria, releen en cada acceso a `/stock`, sin `localStorage` — idéntica a `Productos.jsx`/`useProductos.js` pero sin mutaciones ni `Promise.all`.

```js
// forma del estado en Stock.jsx (análoga a Productos.jsx, propia sin modal)
{
  stock: [],                 // Array<{codigo,nombre,stock_actual,stock_minimo,alerta}> — RF-1
  cargando: false,           // boolean — RF-2 (controla <Loading />)
  error: null,               // {tipo,mensaje,reintentable}|null — RF-2
}
```

`useStock.js` expone — análoga a `useProductos` pero minimal:
- `stock, cargando, error, revalidar()` — RF-1 (`GET /api/v1/stock` sin filtros, orden backend, con filtrado defensivo `esFilaStockValida`)
- `revalidar()` → `GET /stock` → filtra filas válidas → set `stock` (si todas corruptas → `[]`)
- Nunca cachea `localStorage` (constitución §5) — idéntica.
- No expone `crear/editar/baja` — **propia** (solo lectura, a diferencia de `006`/`008`).

> RF-1, RF-2, RNF-3 — **Reutilizado** patrón de `006`/`008`, **propio** sin mutaciones.

## 7. Manejo de valores null — [Cubre RF-1, RNF-1] — *Propia (consistente con 007 §5 y 008 §6 pero adaptada)*

**Regla `spec.md:22,53` (consistencia con `007`/`008` `—` para `null`):**

| Campo | Valor API | Render en `StockTabla.jsx` | Ejemplo |
|-------|-----------|----------------------------|---------|
| `stock_minimo` | `0` (incl. `null→0` por `004`) | `"0"` | `0` → `0` (no `"—"`, valor válido) |
| `stock_minimo` | `5` | `"5"` | — |
| Cualquier otro campo obligatorio `null`/`undefined`/ausente | `null` | **fila omitida** (ver §5), no `"—"` | `alerta null` → fila omitida |
| `alerta` | `true` | badge `"Bajo stock"` + fila marcada | — |
| `alerta` | `false` | `"—"` en celda `alerta` + fila sin marca | — |
| `codigo`/`nombre` | `null` | fila omitida | — |
| `stock_actual` | `null` en contrato válido nunca ocurre; si ocurriera → fila omitida (no `"—"`) | — | — |

- Campos extra `stock_inicial`/`entradas`/`salidas` si son `null` se ignoran (no se muestran).
- Frontend nunca inventa `0` o `"—"` para fila corrupta; la omite.

> RF-1 — **Propia** vs `006` (`stock_inicial` vacío→ausencia) y `007` (`email null→"—"` en tabla pero `""` en form).

## 8. Flujo de carga en pseudocódigo — [Cubre RF-1..2, RNF-2] — *Idéntica a 006 §6 en estados, propia sin 404*

**RF-1 + RF-2 `Stock.jsx` + `useStock.js`** — *Idéntica a `Productos.jsx` pero sin modal y sin caso 404*

```
al montar /stock: cargando=true → <Loading mensaje="Cargando..." />
  GET /api/v1/stock (sin filtros, via stock.js) → 
    200 con [] o null/204 o todas filas corruptas tras filtro → <EmptyState mensaje="Sin datos disponibles">
    200 con array → filtrar esFilaStockValida → si [] tras filtro → <EmptyState> ; else → <StockTabla> 5 cols (codigo|nombre|stock_actual|stock_minimo|alerta con badge "Bajo stock"/"—" y fila marcada si alerta==true)
    4xx (incl. 401) → <ErrorMessage variante="validacion" mensaje=api sin Reintentar>
    conexion/5xx/timeout → <ErrorMessage variante="conexion" mensaje="Error de conexión con el servidor" onReintentar=revalidar />
  App.jsx: /stock → Stock.jsx bajo AppLayout (idéntica a 006/007/008)
  Reintentar deshabilitado mientras cargando; navegar fuera durante cargando no cancela petición, al volver se refleja resultado (idéntica a 008 RF-4)
```

> Nota: sin rama `404` para global (a diferencia de `006` 404 producto no encontrado), porque `004` define global siempre `200` con `[]`. `404` solo existiría en `GET /stock/{codigo}` fuera de alcance.

> Todos usan `Loading`/`EmptyState`/`ErrorMessage` sin variantes y `role="alert"` vs `role="status"` — idéntica a `008`.

## 9. Decisiones técnicas justificadas (y alternativa descartada) — [Cubre RF-1..2, RNF-4]

1. **Tabla `StockTabla.jsx` 5 cols con badge+fila vs solo badge o solo color** — *Propia (no existe en 006/007/008)*
   - Elegida: badge `"Bajo stock"`/`"—"` en columna `alerta` + fila con fondo diferenciado como refuerzo, nunca solo color.
   - Descartada: solo color de fondo sin badge, o solo badge sin fila.
   - Motivo: `RNF-6` accesibilidad — solo color falla para daltónicos y lector de pantalla; badge es texto accesible y fila da refuerzo visual. Ambos juntos cumplen `006`/`008` patrón de `"—"` para `null` y son testeables (`getByText("Bajo stock")` + `class` de fila).

2. **Hook `useStock` minimal (solo lectura) vs reutilizar `useProductos` con `stock_minimo`** — *Propia*
   - Elegida: `useStock.js` con solo `stock,cargando,error,revalidar` y `listarStock`, sin `crear/editar/baja`.
   - Descartada: reutilizar `useProductos` y derivar stock en frontend a partir de `productos` + `movimientos`.
   - Motivo: `RNF-1` fuente de verdad `004` ya calcula `stock_actual` y `alerta`; derivar en frontend duplicaría lógica de `003`/`004` y violaría `AGENTS.md:28` (no duplicar validación de negocio). Hook minimal es más simple para junior y respeta `spec.md:70` "solo lee".

3. **Render defensivo por fila (omitir corrupta) vs mostrar fila con `"—"` o `0` por defecto** — *Propia (no existe en 006/007/008)*
   - Elegida: `esFilaStockValida` filtra tipos y presencia; fila corrupta se omite, si todas corruptas → `EmptyState`.
   - Descartada: mostrar fila corrupta con `0` o `"—"` inventado, o romper render con error.
   - Motivo: evita inventar dato de inventario (`0` podría ocultar quiebre real) y evita `TypeError` en tabla; consistente con `spec.md:52` y principio de no exponer dato falso. `006`/`008` solo mapeaban `null→"—"` para campos opcionales, no omitían fila.

4. **Sin acciones por fila vs botón "Ver detalle" o "Editar mínimo"** — *Propia*
   - Elegida: tabla sin botones, sin `onClick` en fila, sin navegación a `Productos`.
   - Descartada: añadir botón "Editar stock_minimo" o link a `/productos?edit=...`.
   - Motivo: `spec.md:59` fuera de alcance y `HU-2` aclara que el usuario navega manualmente a `Productos`; añadir acción duplicaría flujo de `006` y rompería `RNF-4` solo lectura.

5. **Componente `StockTabla.jsx` presentacional vs lógica en `Stock.jsx`** — *Idéntica a `006` decisión 3 y `008` decisión 3*
   - Elegida: `StockTabla.jsx` recibe `stock: Array` ya filtrado y solo renderiza `<table>` con 5 cols y clases condicionales por `alerta`.
   - Descartada: todo el render y validación dentro de `Stock.jsx`.
   - Motivo: separa presentación de lógica (`AGENTS.md:21`), testeable sin `fetch` mockeado para tabla pura y con `fetch` para `Stock.jsx`.

6. **`stock_minimo 0 → "0"` vs `0 → "—"`** — *Propia (consistencia con 007/008)*
   - Elegida: `0` se muestra como `"0"` (valor válido), `null` genérico como `"—"`, fila con `alerta null` se omite.
   - Descartada: `0` como `"—"` o como vacío.
   - Motivo: `0` es mínimo válido y distinto de ausencia (`null→0` por `004` pero `0` explícito es intencional); `007`/`008` ya usan `"—"` solo para `null` no para `0`.

## 10. Estrategia de tests — [Cubre RF-1..2, RNF-1..6, constitución §4] — *Análoga a 006 §8 y 008 §9*

Stack `Vitest` + `Testing Library` + `user-event` + `jsdom`, `fetch` mockeado vía `client.js` (sin tocar red). No se escribe código de tests aquí.

**`src/api/stock.js` — unidad (análoga a `productos.js`/`movimientos.js`):**
- RF-1: `listarStock` `200` con 5 campos `codigo|nombre|stock_actual|stock_minimo|alerta` (y `alerta` boolean), `[]`→`EmptyState`, `null`/`204`/`[]` tras filtro→`EmptyState`, `401→validacion` sin Reintentar, `500/red/timeout→conexion` con Reintentar, orden `codigo ASC` sin reordenar.
- RNF-1: verifica que `listarStock` no recalcula `alerta` (solo lee campo), y que `stock_minimo` `null` no se hace en `stock.js` (lo hace backend).
- Verificación `grep -r "fetch(" src/components|hooks|pages` vacío y `VITE_API_URL` solo en `client.js` — idéntica a `008`.

**`Stock.jsx` — integración (análoga a `Productos.jsx`/`Movimientos.jsx`):**
- RF-1: monta→`Loading` luego `StockTabla` 5 cols o `EmptyState` si `[]`/`null`/`204`/todas corruptas, con badge `"Bajo stock"`/`"—"` y fila marcada si `alerta==true`.
- RF-1 defensivo: `alerta==true` muestra badge + fila con clase, `alerta==false` muestra `"—"` sin marca; fila con `codigo` number/`alerta` string/`stock_actual` float se omite sin romper resto; si todas corruptas → `EmptyState`.
- RF-2: `4xx` (401) → `ErrorMessage validacion` sin Reintentar y sin tabla; `5xx`/red/timeout → `ErrorMessage conexion` con Reintentar que reejecuta solo `listarStock`; botón Reintentar `disabled` mientras `cargando`; navegar fuera durante `cargando` no cancela.
- RF-2 `null`/`204`: `200` con `null` o `204` → `EmptyState` (no error).
- RNF-3: `localStorage` nunca usado, relee en cada acceso a `/stock`.
- Casos límite propios: `stock_actual` negativo/`>2M` se muestra tal cual con `alerta` del backend, `nombre` largo sin truncar, `codigo` duplicado muestra ambas filas.

**`StockTabla.jsx` — unidad presentacional (análoga a `ProductoTabla`/`MovimientosHistorial`):**
- RF-1: tabla 5 cols `codigo|nombre|stock_actual|stock_minimo|alerta` sin filtros, con `"—"` para `alerta false` y `alerta` true con badge, `stock_minimo 0` como `"0"`, fila con `alerta true` tiene clase de resalte + badge, fila `false` no; `codigo` duplicado renderiza ambas filas.
- A11y: `th` con `scope="col"`, `label` no aplica (sin form), `role="alert"` para `ErrorMessage` en `Stock.jsx` padre; badge texto accesible.

> Criterio `spec.md:72`: `npm run test` verde, `npm run lint` sin errores, `grep` vacíos, español.

## 11. Cobertura de RFs — trazabilidad

| Parte del plan | RF cubierto | Evidencia verificable | Reutilizado de `005`/`006`/`008` |
|---|---|---|---|
| `StockTabla.jsx` 5 cols con badge `"Bajo stock"`/`"—"` + fila marcada si `alerta==true` | RF-1 | tabla 5 cols, `—` para `false`, badge+fila para `true`, `0` como `"0"`, filas corruptas omitidas | Propia (alerta+defensivo) |
| `Stock.jsx` + `useStock` con `Loading`/`EmptyState`/`ErrorMessage` | RF-1, RF-2 | `Loading` `Cargando...`, `EmptyState` para `[]`/`null`/`204`/todas corruptas, orden `codigo ASC` sin reordenar | Sí (análoga `Movimientos` 7 cols → 5 cols) |
| `src/api/stock.js` `listarStock` `GET /api/v1/stock` | RF-1, RF-2 | `200` 5 campos con `alerta` boolean, `401` validacion, `5xx` conexion, `VITE_API_URL` solo `client.js` | Sí (análoga `productos.js`) |
| `useStock` + `client.js` tipado + `Reintentar` | RF-2 | `validacion` sin Reintentar vs `conexion` con Reintentar, `localStorage` vacío, `401` sin redirección, `disabled` mientras `cargando` | Sí (idéntica `008` RF-4) |
| Filtro defensivo `esFilaStockValida` | RF-1 | fila con `codigo` number/`alerta` string omitida, resto normal, todas corruptas → `EmptyState` | Propia (defensivo por fila) |
| `stock_minimo 0→"0"` vs `null→"—"` | RF-1 | `0` mostrado como `"0"` no `"—"`, `alerta false` como `"—"` | Propia (consistencia `007`/`008`) |
| `a11y` `th`/`badge` texto accesible, `role=alert` | RNF-5, RNF-6 | `th` asociados, badge texto no solo color | Sí (idéntica) |
| `api/stock.js` sin `fetch` en componentes | Constitución §3, §5 | `grep` vacío | Sí |

## 12. Fuera de alcance del plan (confirmado)

No se diseña detalle por código `GET /stock/{codigo}`, buscador por `codigo`, filtros por `alerta`/`categoria`/`texto`, ordenamiento distinto a `codigo ASC` (ej. `stock_actual` o `alerta`), paginación `?limit&offset`/`?incluir_inactivos`, valorización, lotes, ubicaciones, edición de `stock_minimo`/`stock_actual` en esta pantalla, push/notificaciones, toasts, tema oscuro, i18n, responsive — tal como `spec.md:59-61`.

## 13. Dudas abiertas

- Ninguna bloqueante tras confirmar `004` expone `alerta` (`specs/004-consulta-stock/spec.md:19-20` y `plan.md:48-72` ya incluyen `alerta` con semántica `stock_minimo>0 && stock_actual<stock_minimo`). La `[NECESITA ACLARACIÓN]` de `RNF-1` queda resuelta y se eliminará al cerrar spec.
- Paginação, filtro `?alerta=true`, vista detalle por código y ordenamiento por `stock_actual` se evaluarán en specs futuras si se requieren.
