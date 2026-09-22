# Tasks 008 — Frontend Movimientos (Alta y Historial)

> Orden de dependencia. Cada tarea 20-30 min. Respetar `frontend/docs/constitution.md:3,5,7` y `frontend/AGENTS.md:20,28`. Reutiliza cliente `src/api/client.js` y componentes base `Loading`/`ErrorMessage`/`EmptyState` de 005 y patrón `006`/`007`. Contratos exactos `003/movimientos/plan.md:3`.

## Fase 1 — API y estado base

- [x] **T01 — Crear `src/api/movimientos.js` con `listarMovimientos()`** — RF-1 — Hecho cuando: `GET /api/v1/movimientos` vía `request('/api/v1/movimientos')` resuelve array 7 campos o `[]` ordenado por `fecha desc + id desc`, sin reordenar frontend, normaliza ruta sin `//`, y `grep -r "fetch(" src/components` vacío; `npm run test` verde para este archivo con fetch mockeado.

- [x] **T02 — Añadir `crearEntrada`, `crearSalida` en `src/api/movimientos.js`** — RF-2, RF-3 — Hecho cuando: `POST /api/v1/movimientos/entradas` envía `{producto_codigo,proveedor_codigo,cantidad,motivo?}` y `POST /api/v1/movimientos/salidas` envía `{producto_codigo,cantidad,motivo?}` sin `proveedor_codigo` (aunque se informe, se omite), `422` cantidad/motivo y `404/400` producto/proveedor inactivo mapean a `validacion`, `5xx/red` a `conexion`, `proveedor` nunca se envía en salida; sin hardcodeo `VITE_API_URL`.

- [x] **T03 — Crear `src/hooks/useMovimientos.js` (historial, selects y revalidación)** — RF-1, RF-4 — Hecho cuando: expone `{movimientos, productos, proveedores, cargandoHistorial, cargandoSelects, errorHistorial, errorSelects, revalidar, cargarSelects}` con `fetch` vía `movimientos.js` + `productos.js`/`proveedores.js` (`Promise.all` para selects), estado solo memoria sin `localStorage`, `revalidar` siempre `GET` historial completo tras alta; `npm run test` con fetch mockeado pasa.

## Fase 2 — Componentes presentacionales

- [x] **T04 — Crear `src/components/MovimientosHistorial.jsx`** — RF-1 — Hecho cuando: renderiza `<table>` con 7 columnas fijas `fecha|producto|proveedor|tipo|cantidad|motivo|id` (muestra "—" para `proveedor/motivo null`, `fecha` ISO sin formateo, sin truncar), sin filtros/paginación/orden, recibe `movimientos` por props, sin `fetch`, con `data-testid` por fila `movimiento-fila-{id}`; test `vitest` render con 2 movimientos muestra 2 filas y 7 celdas con "—".

- [x] **T05 — Crear `src/components/MovimientoFormModal.jsx` con selector Entrada|Salida** — RF-2, RF-3 — Hecho cuando: modal `role="dialog"` `aria-modal` con tabs/radio `Entrada|Salida` (`Entrada` preseleccionada), `Entrada` muestra 4 campos (`producto <select>`, `proveedor <select>`, `cantidad`, `motivo` opcional), `Salida` muestra 3 campos (oculta `proveedor`), `label htmlFor`/`id`, `proveedor` oculto se limpia y no se envía, cambio `Entrada↔Salida` conserva `producto/cantidad/motivo` y limpia errores/`proveedor`, valida solo `cantidad` requerida y entero `>0` (`"1.0"`→"Debe ser un número entero mayor a 0") y `motivo` no vacío tras `trim` (`"   "`→"No puede quedar vacío") sin fetch; `cargando` deshabilita "Crear" y `<select>` muestra `Cargando...` disabled mientras carga, `[]` muestra mensaje puntual y bloquea "Crear".

- [x] **T06 — Manejar estados de carga/error/vacío de `<select>` en `MovimientoFormModal.jsx`** — RF-2 — Hecho cuando: si `productos`/`proveedores` `[]` bloquea "Crear" con mensaje "No hay productos/proveedores activos disponibles", si carga falla `4xx` muestra `ErrorMessage validacion` sin Reintentar y bloquea hasta cerrar/reabrir, si `5xx/red` muestra `ErrorMessage conexion` con Reintentar que reejecuta solo el `GET` del `<select>` fallido; `grep -r "fetch(" src/components` vacío.

## Fase 3 — Página Movimientos y flujos

- [x] **T07 — Crear `src/pages/Movimientos.jsx` con historial (RF-1)** — RF-1 — Hecho cuando: al montar muestra `Loading` ("Cargando..."), luego `MovimientosHistorial` o `EmptyState` ("Sin datos disponibles") si `[]`, o `ErrorMessage` (4xx sin Reintentar vs 5xx/red con Reintentar que re-ejecuta `revalidar`); sin columna stock, con "—" para `null` y `fecha` ISO; `App.jsx` añade ruta `/movimientos→Movimientos.jsx` anidada bajo `AppLayout`.

- [x] **T08 — Integrar flujo alta Entrada en `Movimientos.jsx`** — RF-2, RF-4 — Hecho cuando: click "Crear movimiento" abre modal `Entrada`, submit válido con `producto+proveedor+cantidad` → `crearEntrada` + `cargando` deshabilita "Crear", `4xx` mantiene modal con `ErrorMessage validacion` sin Reintentar, `5xx` con Reintentar, `201` cierra modal + banner "Movimiento registrado correctamente" 3s `role="status"` (reinicia timer si existe) + `revalidar()` `GET`; `cantidad` `"1.0"`/`"   "` bloquea local, `motivo` `"   "` bloquea, `proveedor` vacío bloquea.

- [x] **T09 — Integrar flujo alta Salida en `Movimientos.jsx`** — RF-3, RF-4 — Hecho cuando: tab `Salida` oculta `proveedor` y no lo envía (aunque existía en `Entrada`), `producto+cantidad` requerido, `400` stock insuficiente mantiene modal con mensaje API `Stock insuficiente`, `404` producto inactivo mantiene modal, `5xx` con Reintentar, `201` cierra + mismo banner + `revalidar`; cambio `Entrada→Salida` conserva `producto/cantidad/motivo` y limpia `proveedor`/errores, `Salida→Entrada` deja `proveedor` vacío requiriendo nueva selección.

- [x] **T10 — Manejo uniforme estados, mensajes éxito y revalidación vs fallo** — RF-4 — Hecho cuando: `ErrorMessage` dos niveles sin variantes y `mensajeExito` banner `role="status"` 3s separado coexistiendo con error de revalidación; revalidación tras éxito siempre `GET` completo y si falla muestra error listado manteniendo éxito (banner arriba, `ErrorMessage` debajo); `401` como `validacion` sin redirección ni Reintentar; `grep -r "localStorage"` vacío; múltiples clics en "Crear" solo una petición.

## Fase 4 — Tests y cierre

- [x] **T11 — Tests unidad `src/api/movimientos.js` (Vitest fetch mockeado)** — RF-1..4 — Hecho cuando: `listar` 200/`[]`/401/500 orden `fecha desc`, `crearEntrada` 201/404/400/422 con `proveedor` obligatorio, `crearSalida` 201/400 stock insuficiente/422 sin `proveedor` y nunca envía `proveedor`, `baja` no existe; verifican `fetch` solo en `src/api/` y `VITE_API_URL` solo en `client.js`.

- [x] **T12 — Tests componentes `MovimientosHistorial`/`MovimientoFormModal` (selects condicionados)** — RF-1..3 — Hecho cuando: historial 7 cols con "—" para `null` sin `stock`, modal 4/3 campos según tipo con `tabs` `Entrada|Salida`, `Entrada` preseleccionada, cambio de tipo conserva `producto/cantidad/motivo` y limpia `proveedor`/errores, `[]` bloquea `Crear`, `Cargando...` disabled, `4xx` vs `5xx` en selects, validación `cantidad >0 entero` y `motivo` `No puede quedar vacío` bloquea, a11y `label htmlFor`/`role=dialog`/`aria-modal`/`aria-selected`.

- [x] **T13 — Tests integración `Movimientos.jsx` (historial/alta entrada/alta salida)** — RF-1..4 — Hecho cuando: monta→Loading→Historial/Empty/Error, alta `Entrada` 201 cierra+revalida y `""`/`"   "` bloquea, alta `Entrada` 404 mantiene modal, alta `Salida` sin `proveedor` y `400` stock insuficiente mantiene modal, salida `201` cierra+revalida, `401` como validacion en alta y revalidación, botones deshabilitados cargando, múltiples clics una sola petición, `proveedor` nunca enviado en `Salida`.

- [x] **T14 — Verificación final lint, formato y manual** — Todos RF, RNF-1–6 — Hecho cuando: `npm run lint` sin errores, `npm run format` aplicado, `npm run test` 100% verde, `grep -r "fetch(" src/components src/pages src/hooks` vacío, `grep -r "localStorage"` vacío, `npm run dev` contra backend real muestra historial solo lectura, altas `Entrada` y `Salida` funcionando con `selects` activos, revalidación visible, transición `0→1` y semántica `proveedor` oculto vs `motivo` `""` bloqueado.
