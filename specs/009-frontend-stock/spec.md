# Spec 009 — Frontend Consulta de Stock (Solo Lectura con Alerta)

## Contexto y objetivo
La tienda necesita consultar el stock actual derivado de cada producto para decidir reposiciones, apoyándose en el esqueleto base de `005-frontend-base` (layout con navegación persistente y componentes base de cargando/error/vacío) ya validado en `006`/`007`/`008`. Esta funcionalidad entrega exclusivamente la pantalla de consulta de stock que consume el backend definido en `004-consulta-stock`: interpreta el stock derivado (`stock_actual = stock_inicial + entradas - salidas`) y el flag de alerta para resaltar productos por debajo de su mínimo. Es puramente de solo lectura y no crea ni modifica productos ni movimientos; solo expone datos existentes ya persistidos. Es consumidora directa de `004` y sucesora de `008`, donde se delimitó que `stock_actual` no se visualiza en el historial de movimientos.

## Usuarios
- **Encargado de inventario:** consulta el stock global para identificar qué reponer. Único actor del MVP. Sin autenticación ni roles; mismo operador de tienda de `005`/`006`/`007`/`008`.

## Historias de usuario
- **HU-1:** Como encargado, quiero consultar el listado global de stock actual de todos los productos activos con su stock mínimo y un indicador de alerta para ver de un vistazo qué está por debajo del mínimo.
- **HU-2:** Como encargado, quiero distinguir visualmente los productos en alerta (por debajo del mínimo) para priorizar la reposición sin tener que comparar números manualmente. Al detectar una alerta en esta pantalla, navego manualmente a la pantalla de Productos (`006-frontend-productos`) para ajustar `stock_minimo` si corresponde — esta pantalla no ofrece acción ni navegación directa hacia allá, solo deja claro cuál es el paso siguiente esperado.
- **HU-3:** Como encargado, quiero entender qué pasó cuando la carga del stock falla para corregir o reintentar sin perder contexto.

## Requisitos funcionales

### RF-1 — Consulta global de stock con alerta visual
El sistema debe mostrar el listado global de stock actual derivado, ordenado y con alerta resaltada, en modo solo lectura sin filtros ni paginación.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado acceda a la sección stock, el sistema deberá pedir el listado global a la API (`GET /api/v1/stock` sin filtros ni paginación) y mostrar todos los productos activos tal cual los devuelve la API ordenados por `codigo ASC`, sin reordenar en el frontend, sin filtros en UI, sin paginación y con scroll vertical si crece. Si la API devolviera el listado desordenado (violación de contrato), el sistema lo mostrará tal cual sin reordenar.
  - El sistema deberá mostrar por cada producto las 5 columnas `codigo | nombre | stock_actual | stock_minimo | alerta`, donde `codigo` y `nombre` provienen del catálogo, `stock_actual` es el derivado y `stock_minimo` es el configurado; la columna `alerta` muestra un badge de texto con valor `"Bajo stock"` cuando `alerta == true` y `"—"` cuando `alerta == false`; no deberá mostrar columna de estado ni de inactivos. La columna `alerta` nunca queda vacía.
  - Cuando `alerta == true` (booleano calculado exclusivamente por el backend), el sistema deberá mostrar en la columna `alerta` el badge `"Bajo stock"` y además marcar la fila completa con estado visual diferenciado como refuerzo — nunca solo color de fondo sin el badge, por accesibilidad (el badge es la fuente de verdad para lector de pantalla). Cuando `alerta == false`, el sistema mostrará `"—"` en la columna `alerta` y no aplicará marca visual a la fila. El frontend nunca recalcula `alerta` a partir de `stock_actual`/`stock_minimo`; solo lee el campo `alerta` tal cual.
  - Cuando `stock_minimo` sea `0` (incluido `null` persistido como `0` por `004`), el sistema deberá mostrar `0` en la celda y `alerta == false` (`"—"` sin marca), independientemente de `stock_actual`. Para cualquier otro campo obligatorio con valor `null`, `undefined` o ausente tratado como fila corrupta, aplica el caso límite de fila omitida; para campos no obligatorios no aplica, pues las 5 columnas son obligatorias.
  - El sistema no deberá ofrecer acciones por fila (crear/editar/borrar) ni navegación directa a edición de `stock_minimo`, ni selección de fila; la edición permanece exclusivamente en la pantalla de productos vía catálogo.
  - El sistema deberá mostrar `stock_actual` y `stock_minimo` como número entero decimal sin separador de miles ni formateo localizado adicional; `nombre` y `codigo` se muestran tal cual sin truncar, con salto de línea si es largo.

### RF-2 — Manejo uniforme de estados de la consulta
El sistema debe reutilizar los patrones base de `005` para los estados de la consulta de stock.
- **Criterios de aceptación (EARS):**
  - Mientras se espera la respuesta de la lista global, el sistema deberá mostrar el estado cargando uniforme con texto "Cargando...".
  - Cuando la API devuelva lista vacía `[]` (sin productos activos), el sistema deberá mostrar el estado vacío con mensaje "Sin datos disponibles". El mismo estado se mostrará si la respuesta es `200` con `null`, `204 No Content`, o si todas las filas fueron omitidas por datos corruptos.
  - Cuando la API responda con error `4xx` (incluido `401`), el sistema deberá mostrar el mensaje específico devuelto por la API sin botón Reintentar; cuando sea error de red, timeout o `5xx`, deberá mostrar "Error de conexión con el servidor" con botón "Reintentar" que reejecute solo la carga global de stock (`GET /api/v1/stock`). El listado global nunca devuelve `404` — según `specs/004-consulta-stock/spec.md:22` siempre responde `200` con `[]` si no hay activos; `404` solo aplicaría al detalle por código, fuera de alcance.
  - Si la API responde con `401`, el sistema deberá tratarlo como cualquier otro `4xx` mostrando el mensaje de la API sin redirección y sin Reintentar.
  - Mientras cualquier carga esté en curso, el sistema deberá deshabilitar su botón disparador (Reintentar) para evitar reintentos duplicados por doble clic. Si el usuario navega fuera mientras carga, la petición en curso no se cancela y al volver se refleja el resultado tras revalidación.

## Requisitos no funcionales
- **RNF-1 — Fuente de verdad API:** el frontend no calcula `stock_actual` ni `alerta`; solo los expone tal cual los entrega `004` vía `GET /api/v1/stock`, incluido el campo `alerta` booleano ya calculado por el backend. El frontend NUNCA recalcula la fórmula `stock_minimo > 0 && stock_actual < stock_minimo` (con `<` estricto, `==` no dispara, `0` nunca alerta); la fórmula se documenta solo para que los tests verifiquen el `alerta` recibido, no para implementarla. `stock_minimo` entre `0..1_000_000` y `null→0` los decide el backend. [NECESITA ACLARACIÓN] Confirmar que el contrato de `specs/004-consulta-stock/spec.md` y su `plan.md` exponen efectivamente el campo `alerta` boolean en `GET /api/v1/stock`; si no, definir su forma exacta antes de implementar.
- **RNF-2 — Reutilización de base 005/006/007/008:** la consulta usa los mismos patrones de `Loading` ("Cargando..."), `EmptyState` ("Sin datos disponibles") y `ErrorMessage` con dos niveles (4xx sin Reintentar vs red/5xx con Reintentar) sin variantes; sin lógica de paginación o filtros propia. Toda comunicación HTTP usa el cliente centralizado (constitución frontend §3, `AGENTS.md:20`).
- **RNF-3 — Estado solo en memoria:** sin persistencia en cliente (`localStorage`/`sessionStorage` prohibidos para inventario); todo dato se relee de la API en cada acceso a la sección (constitución frontend §5).
- **RNF-4 — Mantenibilidad junior:** pantalla puramente de solo lectura en misma ruta, sin estado global, sin ordenamiento ni búsqueda en el frontend.
- **RNF-5 — Mensajes en español:** navegación, encabezados de tabla, estados y errores breves en español; los dos genéricos de `005` sin variantes; los mensajes `4xx` de `004` ya son en español y se muestran tal cual.
- **RNF-6 — Accesibilidad mínima:** tabla con encabezados asociados a celdas (`th`/`td`), foco visible, navegación por teclado, `role="alert"` para errores y badge `"Bajo stock"` como texto accesible para el resalte (no solo color); no se exige WCAG completo.

## Casos límite
- Listado vacío legítimo (0 productos activos, aunque existan inactivos con stock) → `[]` → `EmptyState` "Sin datos disponibles"; transición de `0→1` tras crear primer producto y consultarlo muestra fila sin resalte si `alerta == false`.
- Producto sin movimientos con `stock_inicial 5` y `stock_minimo 10` → `stock_actual 5` y `alerta true` con badge+fila marcada; con `stock_inicial 0` y `stock_minimo 0` → `0` y `false` sin marca.
- `alerta == false` con `stock_actual == stock_minimo` (ej. 5/5) → sin marca (solo `<` dispara en backend); `stock_actual 0` con `stock_minimo 5` → `true` con marca; `stock_minimo 0` con cualquier `stock_actual` → `false` sin marca.
- Producto con `stock_minimo null` persistido como `0` → mostrar `0` y `"—"` en `alerta` sin marca.
- Carga inicial falla con `401` → `ErrorMessage` validación sin Reintentar, sin `EmptyState`, sin tabla; botón Reintentar no visible; al corregir sesión el usuario reintenta vía navegación. `404` no aplica al listado global (siempre `200` con `[]`); solo aplicaría al detalle por código, fuera de alcance.
- Respuesta `4xx` sin mensaje o cuerpo no JSON → genérico validación "No se pudo completar la solicitud. Revisa los datos e intenta nuevamente." sin Reintentar; `5xx`/red/timeout → genérico conexión con Reintentar.
- Listado global con cientos/miles de filas → scroll vertical sin paginación ni virtualización en MVP, orden `codigo ASC` garantizado por backend, frontend no reordena; si backend desordena, se muestra tal cual.
- Múltiples clics rápidos en `Reintentar` → botón `disabled` mientras `cargando`, sin duplicados locales; navegación fuera durante `cargando` no cancela petición.
- Fila con tipo de dato incorrecto (`stock_actual` string/float, `alerta` string, `codigo` número) o con campo obligatorio faltante/`null`/`undefined` (`codigo`, `nombre`, `stock_actual`, `stock_minimo`, `alerta`) → esa fila se omite del render sin inventar valor por defecto (`0` o `"—"`) y el resto de la tabla se muestra con normalidad; si todas las filas son corruptas, se muestra `EmptyState` (equivalente a `[]`). Campos extra no contemplados en el contrato (ej. `stock_inicial`, `entradas`, `salidas`) se ignoran sin validarlos ni mostrarlos.
- Valor `null` en campo mostrado → mostrar `"—"`, excepto `stock_minimo == 0` que se muestra como `"0"` (valor válido distinto de ausencia), consistente con `007`/`008`. `stock_actual` nunca es `null` en contrato válido; si lo fuera, la fila se omite según caso anterior, no se muestra `"—"`.
- Respuesta `200` con `null` en lugar de `[]`, `204 No Content`, o `Content-Type` no JSON para éxito → tratar como `[]` y mostrar `EmptyState`.
- `stock_actual` negativo o `>2_000_000` (ej. `1_000_000 + 1_000_000` `specs/004-consulta-stock/spec.md:38`) → mostrar el número tal cual sin clamping, y respetar `alerta` del backend para el resalte.
- `nombre` o `codigo` muy largo (20 chars) → mostrar completo sin truncar, con salto de línea, sin `overflow` oculto.
- `codigo` duplicado en listado → mostrar ambas filas tal cual (clave de render por `codigo` + índice), sin deduplicar.

## Fuera de alcance
- Detalle puntual por código (`GET /api/v1/stock/{codigo}`) y buscador por código; el MVP muestra solo el listado global `GET /api/v1/stock` completo (sin paginación) y sin vista unitaria.
- Creación, edición o borrado de productos, movimientos o de `stock_minimo`/`stock_actual` desde esta pantalla; `stock_minimo` se edita exclusivamente vía catálogo de productos (`006`).
- Filtros por `alerta=true`, por categoría, por texto, y ordenamiento distinto a `codigo ASC` (ej. ordenar por `stock_actual` o por alerta); la API global siempre devuelve solo `activos` ordenados por `codigo`.
- Paginación (`?limit&offset`), `?incluir_inactivos`, valorización económica, lotes, ubicaciones y reportes agregados.
- Alertas push, notificaciones, toasts globales, tema oscuro, internacionalización y adaptación responsive dedicada.
- Autenticación/autorización (401 como 4xx estándar).

## Criterios de finalización
- RF-1 y RF-2 verificados según EARS: listado global `codigo|nombre|stock_actual|stock_minimo|alerta` (5 columnas) ordenado `codigo ASC` sin reordenar en frontend, con columna `alerta` con badge `"Bajo stock"`/`"—"` y fila marcada como refuerzo (nunca solo color) para `alerta == true` leído del backend, sin resalte para `alerta == false`; `stock_minimo null→0` mostrado como `"0"` y `null` genérico como `"—"`; filas corruptas omitidas (todas corruptas → `EmptyState`); sin filtros/paginación/acciones por fila/borrado/edición y sin columna de estado.
- Estados `Loading` ("Cargando...") / `EmptyState` ("Sin datos disponibles" incluyendo `null`/`204`/todas corruptas) / `ErrorMessage` (4xx mensaje API sin Reintentar vs red/5xx genérico con Reintentar que reejecuta solo el listado global `GET /api/v1/stock`) reutilizando `005`, con `401` sin redirección y botón deshabilitado mientras `cargando`, y navegación fuera sin cancelar.
- Sin persistencia en cliente; todo dato releído de la API en cada acceso; `stock_actual` y `alerta` no recalculados en el frontend (solo leídos).
- Sin detalle por código, sin filtros por alerta/categoría, sin paginación, sin orden por stock y sin `inactivos` incluidos.
- Pruebas de componente para consulta global (cargando/vacío/error/alerta con badge+fila) con `fetch` mockeado vía cliente centralizado según constitución frontend §4 y `AGENTS.md:20`: `npm run test` verde y `npm run lint` sin errores; `grep -r fetch` vacío fuera de `src/api`, `grep -r localStorage` vacío.
- `npm run dev` contra backend real muestra pantalla de stock en solo lectura, con listado global y alertas resaltadas correctamente, y manejo de `0` vs `<` según `004`.
- Spec aprobada salvo [NECESITA ACLARACIÓN] bloqueante sobre campo `alerta` en `004` (ver Dudas).

## Dudas abiertas
- [NECESITA ACLARACIÓN] Confirmar que `specs/004-consulta-stock/spec.md` y su `plan.md` exponen el campo `alerta` boolean en `GET /api/v1/stock` con la semántica `stock_minimo > 0 && stock_actual < stock_minimo`; si no, definir forma exacta antes de implementar. Es la única bloqueante.
- Ninguna otra bloqueante; paginación, filtro `?alerta=true`, vista detalle por código y ordenamiento por `stock_actual` se evaluarán en specs futuras si se requieren.
