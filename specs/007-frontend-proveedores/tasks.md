# Tasks 007 — Frontend Proveedores (Gestión de Catálogo)

> Orden de dependencia. Cada tarea 20-30 min. Respetar `frontend/docs/constitution.md:3,5,7` y `frontend/AGENTS.md:20,28`. Reutiliza cliente `src/api/client.js` y componentes base `Loading`/`ErrorMessage`/`EmptyState` de 005 y patrón `006`. Contratos exactos `002/proveedores/plan.md:3`.

## Fase 1 — API y estado base

- [x] **T01 — Crear `src/api/proveedores.js` con `listarProveedores()`** — RF-1 — Hecho cuando: `GET /api/v1/proveedores` vía `request('/api/v1/proveedores')` resuelve array 5 campos o `[]` ordenado por `codigo`, normaliza ruta sin `//`, y `grep -r "fetch(" src/components` vacío; `npm run test` verde para este archivo con fetch mockeado.

- [x] **T02 — Añadir `crearProveedor`, `editarProveedor`, `bajaProveedor` en `src/api/proveedores.js`** — RF-2, RF-3, RF-4 — Hecho cuando: `POST /api/v1/proveedores` envía `{codigo,nombre,email?,telefono?,direccion?}` (opcional ausente→omitido, `null`→`null`), `PATCH /{codigo}` envía solo campos con intención (`null` borra, ausente conserva, `""` nunca se envía), `DELETE /{codigo}`; 409/400/422 mapean a `validacion`, 5xx/red a `conexion`; sin hardcodeo `VITE_API_URL`.

- [x] **T03 — Crear `src/hooks/useProveedores.js` (listado y revalidación)** — RF-1, RF-5 — Hecho cuando: expone `{proveedores, cargandoListado, errorListado, revalidar}` con `fetch` vía `proveedores.js`, estado solo memoria sin `localStorage`, `revalidar` siempre `GET` tras mutación; `npm run test` con fetch mockeado pasa.

## Fase 2 — Componentes presentacionales

- [x] **T04 — Crear `src/components/ProveedorTabla.jsx`** — RF-1 — Hecho cuando: renderiza `<table>` con 5 columnas fijas `codigo|nombre|email|telefono|direccion` (muestra "—" para `null`), sin filtros/paginación/orden, recibe `proveedores` y `onEditar`/`onBaja` por props, sin `fetch`, con `data-testid` por fila; test `vitest` render con 2 proveedores muestra 2 filas y 5 celdas con "—".

- [x] **T05 — Crear `src/components/ProveedorFormModal.jsx` modo alta** — RF-2 — Hecho cuando: modal `role="dialog"` `aria-modal` con 5 campos (`codigo` texto, `nombre` texto, `email`/`telefono`/`direccion` opcionales), `label htmlFor`/`id`, valida solo presencia tras `trim` para `codigo`/`nombre` y opcional no vacío tras `trim` (muestra "Código requerido"/"Nombre requerido"/"No puede quedar vacío" inline sin fetch); prop `cargando` deshabilita "Crear".

- [x] **T06 — Extender `ProveedorFormModal.jsx` para modo edición con semántica null** — RF-3 — Hecho cuando: modo `edicion` precarga `nombre/email/telefono/direccion` (`null`→`""` vacío), `codigo` visible `disabled` y excluido del payload; botón "Borrar" por campo opcional envía `null` explícito, campo no tocado se omite, `""`/`"   "` bloquea local sin fetch; test `SKU` deshabilitado y `null` vs `""` vs ausente.

- [x] **T07 — Crear `src/components/ProveedorBajaDialog.jsx`** — RF-4 — Hecho cuando: `role="dialog"` muestra "¿Dar de baja a <nombre> (<codigo>)? No se puede deshacer..." con Confirmar/Cancelar, `Confirmar` deshabilitado si `cargando`, ESC/cancelar cierra sin fetch, sin `fetch` directo.

## Fase 3 — Página Proveedores y flujos

- [x] **T08 — Crear `src/pages/Proveedores.jsx` con listado (RF-1)** — RF-1 — Hecho cuando: al montar muestra `Loading` ("Cargando..."), luego `ProveedorTabla` o `EmptyState` ("Sin datos disponibles") si `[]`, o `ErrorMessage` (4xx mensaje API sin Reintentar vs 5xx/red "Error de conexión..." con Reintentar que re-ejecuta `revalidar`); sin columna estado y con "—" para `null`; `App.jsx` añade ruta `/proveedores→Proveedores.jsx` anidada bajo `AppLayout`.

- [x] **T09 — Integrar flujo alta en `Proveedores.jsx`** — RF-2, RF-5 — Hecho cuando: click "Crear proveedor" abre modal alta, submit válido → `crearProveedor` + `cargando` deshabilita botón, 4xx mantiene modal con `ErrorMessage validacion` mensaje API, 5xx muestra `conexion` con Reintentar, 201 cierra modal + banner "Proveedor creado correctamente" 3s + `revalidar()` `GET`; opcional `""`/`"   "` bloquea local, `null`/ausente no se envía.

- [x] **T10 — Integrar flujo edición en `Proveedores.jsx`** — RF-3, RF-5 — Hecho cuando: click "Editar" abre modal edición con datos precargados (`null`→`""`), botón "Borrar" envía `null`, campo no tocado se omite, `""`/`"   "` bloquea sin fetch, payload vacío sin cambios bloquea "Sin cambios", submit → `editarProveedor(codigo, {nombre,email,telefono,direccion})` sin `codigo`/`estado`, 4xx mantiene modal con mensaje API (ej. ya inactivo/404/`""`), 5xx con Reintentar, 200 cierra + banner "Proveedor actualizado correctamente" + revalidar.

- [x] **T11 — Integrar flujo baja en `Proveedores.jsx`** — RF-4, RF-5 — Hecho cuando: click "Dar de baja" abre diálogo, cancelar/ESC cierra sin fetch, confirmar → `bajaProveedor(codigo)` deshabilita Confirmar, 4xx mantiene diálogo con mensaje API (ya inactivo/404), 5xx con Reintentar, 200 cierra + banner "Proveedor dado de baja correctamente" + revalidar; si revalidado 1→0 muestra `EmptyState`; navegar/cerrar durante cargando no cancela petición; permite baja aunque tenga movimientos.

- [x] **T12 — Manejo uniforme estados, mensajes éxito y revalidación vs fallo** — RF-5 — Hecho cuando: `ErrorMessage` dos niveles sin variantes y `mensajeExito` banner `role="status"` 3s separado coexistiendo con error de revalidación; revalidación tras éxito siempre `GET` y si falla muestra error listado manteniendo éxito; `401` como `validacion` sin redirección; `grep -r "localStorage"` vacío; `email` `TEST@EXAMPLE.COM` aceptado y normalizado a minúsculas en backend.

## Fase 4 — Tests y cierre

- [x] **T13 — Tests unidad `src/api/proveedores.js` (Vitest fetch mockeado)** — RF-1..5 — Hecho cuando: `listar` 200/[]/404/500 ordenado por `codigo`, `crear` 201/409/422 con `email`/`telefono` `null`/ausente/`""`, `editar` `PATCH` `null` borra/ausente conserva/`""` nunca enviado/payload vacío, `baja` DELETE; verifican `fetch` solo en `src/api/` y `VITE_API_URL` solo en `client.js`.

- [x] **T14 — Tests componentes `ProveedorTabla`/`ProveedorFormModal`/`ProveedorBajaDialog`** — RF-1..4 — Hecho cuando: tabla 5 columnas con "—" para `null` sin estado, modal alta 5 campos + validación presencia + `""` bloquea, modal edición `codigo` deshabilitado + botón "Borrar" envía `null`, diálogo texto confirmación, a11y `label htmlFor`/`role=dialog`/`aria-modal`.

- [x] **T15 — Tests integración `Proveedores.jsx` (listado/alta/edición/baja)** — RF-1..5 — Hecho cuando: monta→Loading→Tabla/Empty/Error, alta 201 cierra+revalida y `""`/`"   "` bloquea, alta 409 mantiene modal, edición precarga `null`→`""` y `null` borra vs `""` bloquea vs ausente conserva y PATCH sin `codigo`, baja confirmación y 200→EmptyState 1→0, botones deshabilitados cargando, múltiples clics una sola petición, `401` como validacion.

- [x] **T16 — Verificación final lint, formato y manual** — Todos RF, RNF-1–6 — Hecho cuando: `npm run lint` sin errores, `npm run format` aplicado, `npm run test` 100% verde, `grep -r "fetch(" src/components src/pages src/hooks` vacío, `grep -r "localStorage"` vacío, `npm run dev` contra backend real muestra 4 operaciones, revalidación visible, transición a EmptyState y semántica `null` vs `""` vs ausente.


  Session   Implementar T10 specs/008-frontend-movimientos
  Continue  opencode -s ses_f458c93d1ffeGVgxUjzH40xGeH