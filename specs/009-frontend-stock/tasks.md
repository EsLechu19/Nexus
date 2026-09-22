# Tasks 009 — Frontend Stock (Consulta con Alerta)

> Orden de dependencia. Cada tarea 20-30 min. Respetar `frontend/docs/constitution.md:3,5,7` y `frontend/AGENTS.md:20,28`. Reutiliza cliente `src/api/client.js` y componentes base `Loading`/`ErrorMessage`/`EmptyState` de 005 y patrón `006`/`007`/`008`. Contratos exactos `004-consulta-stock/plan.md:3` (GET /api/v1/stock, campo `alerta` boolean ya calculado).

## Fase 1 — API y estado base

- [x] **T01 — Crear `src/api/stock.js` con `listarStock()`** — RF-1, RF-2 — Hecho cuando: `GET /api/v1/stock` vía `request('/api/v1/stock')` resuelve array 5 campos `codigo|nombre|stock_actual|stock_minimo|alerta` (boolean) o `[]` ordenado `codigo ASC` sin reordenar frontend, incluye `alerta` leído tal cual sin recalcular fórmula, ignora `stock_inicial|entradas|salidas`, y `grep -r "fetch(" src/components src/pages src/hooks` vacío; `npm run test` verde para este archivo con fetch mockeado.

- [x] **T02 — Crear `src/hooks/useStock.js` con `esFilaStockValida` y revalidación** — RF-1, RF-2 — Hecho cuando: expone `{stock, cargando, error, revalidar}` con `fetch` vía `stock.js` + `esFilaStockValida` que verifica tipos/presencia de `codigo,nombre,stock_actual,stock_minimo,alerta` y omite fila corrupta sin romper resto (todas corruptas → `[]`), `null`/`204` → `EmptyState`, sin `localStorage`/`sessionStorage`, `revalidar` siempre `GET` completo; `npm run test` con fetch mockeado pasa.

## Fase 2 — Componentes presentacionales

- [x] **T03 — Crear `src/components/StockTabla.jsx`** — RF-1 — Hecho cuando: renderiza `<table>` con 5 columnas fijas `codigo|nombre|stock_actual|stock_minimo|alerta` (badge `"Bajo stock"` si `alerta==true` + fila con marca visual, `"—"` si `alerta==false` sin marca, `stock_minimo 0`→`"0"` no `"—"`, `nombre`/`codigo` sin truncar con salto de línea), sin filtros/paginación/acciones, recibe `stock` ya filtrado por props, sin `fetch`, con `data-testid` por fila `stock-fila-{codigo}`; test `vitest` render con 2 filas muestra badge+fila marcada y `"—"`.

- [x] **T04 — Manejar `null` y filas corruptas en `StockTabla.jsx`** — RF-1 — Hecho cuando: `stock_minimo 0` muestra `"0"` no `"—"`, `alerta true` aplica badge+fila marcada nunca solo color, `alerta false` muestra `"—"` sin marca, fila con `codigo` number/`alerta` string/`stock_actual` float/`null` se omite sin inventar `0`/`"—"`, campos extra `stock_inicial|entradas|salidas` ignorados, `grep -r "fetch(" src/components` vacío.

## Fase 3 — Página Stock y flujos

- [x] **T05 — Crear `src/pages/Stock.jsx` con estados (RF-1, RF-2)** — RF-1, RF-2 — Hecho cuando: al montar muestra `Loading` ("Cargando..."), luego `StockTabla` o `EmptyState` ("Sin datos disponibles") si `[]`/`null`/`204`/todas corruptas filtradas, o `ErrorMessage` (4xx incluido `401` sin Reintentar vs 5xx/red/timeout con Reintentar que re-ejecuta `revalidar` `GET /api/v1/stock`); sin columna estado/inactivos, con 5 cols badge+fila; `App.jsx` añade ruta `/stock→Stock.jsx` anidada bajo `AppLayout` (sin reordenar, con scroll vertical).

- [x] **T06 — Integrar revalidación y defensivo en `Stock.jsx`** — RF-1, RF-2 — Hecho cuando: `revalidar` filtra `esFilaStockValida` tras `listarStock`, si todas corruptas muestra `EmptyState`, `alerta` nunca recalculada (solo lee campo), `cargando` deshabilita `Reintentar`, navegar fuera durante `cargando` no cancela petición y al volver se refleja resultado; `grep -r "localStorage"` vacío.

## Fase 4 — Tests y cierre

- [x] **T07 — Tests unidad `src/api/stock.js` (Vitest fetch mockeado)** — RF-1, RF-2 — Hecho cuando: `listar` 200 con `alerta` boolean/`[]`/`null`/`204`/401/500 orden `codigo ASC` sin reordenar, nunca recalcula `alerta`, ignora `stock_inicial|entradas|salidas`, filas corruptas omitidas a nivel hook (no aquí), `404` nunca en global; verifican `fetch` solo en `src/api/` y `VITE_API_URL` solo en `client.js`.

- [x] **T08 — Tests componentes `StockTabla`/`Stock` (alerta, defensivo, null)** — RF-1, RF-2 — Hecho cuando: tabla 5 cols con badge `"Bajo stock"`/`"—"` y fila marcada si `alerta==true` vs sin marca si `false`, `stock_minimo 0`→`"0"`, fila con tipo incorrecto omitida sin romper resto, `EmptyState` si todas corruptas, `4xx` sin Reintentar vs `5xx` con Reintentar, `null`→`"—"`, a11y `th`/`badge` texto accesible, `role="alert"` para errores.

- [x] **T09 — Tests integración `Stock.jsx` (cargando/vacío/error/alerta)** — RF-1, RF-2 — Hecho cuando: monta→Loading→StockTabla/Empty/Error, `alerta true` badge+fila y `false` `"—"` sin marca, `stock_minimo 0`→`"0"`, `401` sin Reintentar, `5xx` con Reintentar que re-ejecuta `GET /api/v1/stock`, `204`/`null`→EmptyState, botones deshabilitados cargando, navegación fuera no cancela, filas corruptas omitidas.

- [x] **T10 — Verificación final lint, formato y manual** — Todos RF, RNF-1–6 — Hecho cuando: `npm run lint` sin errores, `npm run format` aplicado, `npm run test` 100% verde, `grep -r "fetch(" src/components src/pages src/hooks` vacío, `grep -r "localStorage"` vacío, `npm run dev` contra backend real muestra listado global `codigo ASC` con 5 cols, alertas badge+fila, `null`→`"—"` vs `0`, y filas corruptas omitidas sin romper tabla.
