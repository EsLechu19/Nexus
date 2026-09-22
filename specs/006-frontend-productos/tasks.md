# Tasks 006 — Frontend Productos (Gestión de Catálogo)

> Orden de dependencia. Cada tarea 20-30 min. Respetar `frontend/docs/constitution.md:3,5,7` y `frontend/AGENTS.md:20,28`. Reutiliza cliente `src/api/client.js` y componentes base `Loading`/`ErrorMessage`/`EmptyState` de 005. Contratos exactos `001/productos-catalogo/plan.md:3`.

## Fase 1 — API y estado base

- [x] **T01 — Crear `src/api/productos.js` con `listarProductos()`** — RF-1 — Hecho cuando: `GET /api/v1/productos` vía `request('/api/v1/productos')` resuelve array 4 campos o `[]`, normaliza ruta sin `//`, y `grep -r "fetch(" src/components` vacío; `npm run test` verde para este archivo con fetch mockeado.

- [x] **T02 — Añadir `crearProducto`, `editarProducto`, `bajaProducto` en `src/api/productos.js`** — RF-2, RF-3, RF-4 — Hecho cuando: `POST /api/v1/productos` envía `{nombre,sku,categoria,stock_inicial?}` (vacío→ausencia), `PATCH /api/v1/productos/{sku}` solo `{nombre,categoria}`, `DELETE /{sku}`; 409/400/404 mapean a `validacion`, 5xx/red a `conexion`; sin hardcodeo `VITE_API_URL`.

- [x] **T03 — Crear `src/hooks/useProductos.js` (listado y revalidación)** — RF-1, RF-5 — Hecho cuando: expone `{productos, cargandoListado, errorListado, revalidar}` con `fetch` vía `productos.js`, estado solo memoria sin `localStorage`, `revalidar` siempre `GET` tras mutación; `npm run test` con fetch mockeado pasa.

## Fase 2 — Componentes presentacionales

- [x] **T04 — Crear `src/components/ProductoTabla.jsx`** — RF-1 — Hecho cuando: renderiza `<table>` con 4 columnas fijas `sku|nombre|categoria|stock_inicial`, sin filtros/paginación/orden, recibe `productos` y `onEditar`/`onBaja` por props, sin `fetch`, con `data-testid` por fila; test `vitest` render con 2 productos muestra 2 filas y 4 celdas.

- [x] **T05 — Crear `src/components/ProductoFormModal.jsx` modo alta** — RF-2 — Hecho cuando: modal `role="dialog"` `aria-modal` con 4 campos (`nombre` texto, `SKU` texto, `categoria` select `videojuego|consola|accesorio`, `stock_inicial` numérico opcional), `label htmlFor`/`id`, valida solo presencia tras `trim` (muestra "Nombre requerido"/"SKU requerido"/"Categoría requerida" inline sin fetch), `stock` vacío no bloquea; prop `cargando` deshabilita "Crear".

- [x] **T06 — Extender `ProductoFormModal.jsx` para modo edición** — RF-3 — Hecho cuando: modo `edicion` precarga `nombre`/`categoria`, `SKU` visible `disabled` y excluido del payload (solo envía `nombre`/`categoria`), `stock_inicial` oculto, validación solo presencia; test `SKU` deshabilitado y no enviado.

- [x] **T07 — Crear `src/components/ProductoBajaDialog.jsx`** — RF-4 — Hecho cuando: `role="dialog"` muestra "¿Dar de baja a <nombre> (<SKU>)? No se puede deshacer..." con Confirmar/Cancelar, `Confirmar` deshabilitado si `cargando`, ESC/cancelar cierra sin fetch, sin `fetch` directo.

## Fase 3 — Página Productos y flujos

- [x] **T08 — Crear `src/pages/Productos.jsx` con listado (RF-1)** — RF-1 — Hecho cuando: al montar muestra `Loading` ("Cargando..."), luego `ProductoTabla` o `EmptyState` ("Sin datos disponibles") si `[]`, o `ErrorMessage` (4xx mensaje API sin Reintentar vs 5xx/red "Error de conexión..." con Reintentar que re-ejecuta `revalidar`); sin columna estado; `App.jsx` añade ruta `/productos→Productos.jsx` anidada bajo `AppLayout`.

- [x] **T09 — Integrar flujo alta en `Productos.jsx`** — RF-2, RF-5 — Hecho cuando: click "Crear producto" abre modal alta, submit válido → `crearProducto` + `cargando` deshabilita botón, 4xx mantiene modal con `ErrorMessage validacion` mensaje API, 5xx muestra `conexion` con Reintentar, 201 cierra modal + banner "Producto creado correctamente" 3s + `revalidar()` `GET`; `stock_inicial` vacío enviado como ausencia.

- [x] **T10 — Integrar flujo edición en `Productos.jsx`** — RF-3, RF-5 — Hecho cuando: click "Editar" abre modal edición con datos precargados, inactivo sin botón Editar (defensivo), submit → `editarProducto(sku, {nombre,categoria})` sin `sku`, 4xx mantiene modal con mensaje API (ej. ya inactivo/404), 5xx con Reintentar, 200 cierra + banner "Producto actualizado correctamente" + revalidar.

- [x] **T11 — Integrar flujo baja en `Productos.jsx`** — RF-4, RF-5 — Hecho cuando: click "Dar de baja" abre diálogo, cancelar cierra, confirmar → `bajaProducto(sku)` deshabilita Confirmar, 4xx mantiene diálogo con mensaje API, 5xx con Reintentar, 200 cierra + banner "Producto dado de baja correctamente" + revalidar; si revalidado 1→0 muestra `EmptyState`; navegar/cerrar durante cargando no cancela petición.

- [x] **T12 — Manejo uniforme estados, mensajes éxito y revalidación vs fallo** — RF-5 — Hecho cuando: `ErrorMessage` dos niveles sin variantes y `mensajeExito` banner separado; revalidación tras éxito siempre `GET` y si falla muestra error listado manteniendo éxito; 401 como `validacion` sin redirección; `grep -r "localStorage"` vacío.

## Fase 4 — Tests y cierre

- [x] **T13 — Tests unidad `src/api/productos.js` (Vitest fetch mockeado)** — RF-1..5 — Hecho cuando: `listar` 200/[]/404/500, `crear` 201/409/400/500 con `stock` ausencia, `editar` solo `nombre/categoria`, `baja` DELETE; verifican `fetch` solo en `src/api/`.

- [x] **T14 — Tests componentes `ProductoTabla`/`ProductoFormModal`/`ProductoBajaDialog`** — RF-1..4 — Hecho cuando: tabla 4 columnas sin estado, modal alta 4 campos + validación presencia, modal edición SKU deshabilitado, diálogo texto confirmación, a11y `label htmlFor`/`role=dialog`.

- [x] **T15 — Tests integración `Productos.jsx` (listado/alta/edición/baja)** — RF-1..5 — Hecho cuando: monta→Loading→Tabla/Empty/Error, alta 201 cierra+revalida, alta 409 mantiene modal, edición precarga y PATCH sin sku, baja confirmación y 200→EmptyState 1→0, botones deshabilitados cargando, múltiples clics una sola petición, `401` como validacion.

- [x] **T16 — Verificación final lint, formato y manual** — Todos RF, RNF-1–6 — Hecho cuando: `npm run lint` sin errores, `npm run format` aplicado, `npm run test` 100% verde, `grep -r "fetch(" src/components src/pages src/hooks` vacío, `npm run dev` contra backend real muestra 4 operaciones, revalidación y transición a EmptyState.
