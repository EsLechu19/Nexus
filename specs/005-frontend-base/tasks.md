# Tasks 005 — Base / Esqueleto Frontend

> Orden de dependencia. Cada tarea 20-30 min. Respetar `frontend/docs/constitution.md:3,5,7` y `frontend/AGENTS.md:15-27`. No implementar CRUD 006-009.

## Fase 1 — Estructura y ruteo

- [x] **T01 — Crear estructura de carpetas `frontend/src/`** — RF-1, RF-2, RF-3, RF-5 — Hecho cuando: existen `src/api/`, `src/components/`, `src/layout/`, `src/pages/`, `src/hooks/` vacías y documentadas en README interno, sin código aún.

- [x] **T02 — Solicitar aprobación e instalar `react-router-dom` v6** — RF-1, RF-2 — Hecho cuando: `package.json` incluye `react-router-dom` con justificación en PR (excepción `AGENTS.md:27`), `npm install` sin errores y `npm run lint` pasa.

- [x] **T03 — Crear `AppLayout.jsx` + `NavLinkItem.jsx` (layout persistente)** — RF-1 — Hecho cuando: renderiza `<header>`, `<nav aria-label="Navegación principal">` con 4 enlaces (Productos/Proveedores/Movimientos/Stock) y `<main id="contenido-principal">` con `<Outlet>`, activo marca `aria-current="page"` y `focus-visible:ring`, `grep fetch` en layout vacío.

- [x] **T04 — Configurar `App.jsx` con mapa de rutas y redirección** — RF-1, RF-2 — Hecho cuando: `/` redirige a `/productos`, `/productos|/proveedores|/movimientos|/stock` → placeholder, `*` → 404, todo anidado bajo `AppLayout`, navegación no recarga layout y preserva URL.

## Fase 2 — Cliente API centralizado

- [x] **T05 — Implementar `src/api/client.js` (lectura y validación `VITE_API_URL`)** — RF-3, RF-4 — Hecho cuando: lee solo `import.meta.env.VITE_API_URL`, aplica `trim()`, valida URL absoluta http/https vía `URL`, marca `configInvalida` si ausente/vacía/espacios/inválida sin hardcodear, `.env.example` actualizado.

- [x] **T06 — Implementar normalización y `request()` con timeout 10s** — RF-3, RF-4, RF-5 — Hecho cuando: normaliza barra final (`/`), usa `fetch` + `AbortController` 10s, headers `Content-Type/Accept: application/json`, `grep -r "fetch(" src/components src/layout src/pages src/hooks` vacío y solo `src/api/` contiene `fetch`.

- [x] **T07 — Implementar propagación tipada de errores 4xx vs conexión/5xx** — RF-5 — Hecho cuando: 4xx (incluido 401) retorna `{tipo:'validacion', reintentable:false, mensaje}` con texto API o genérico validación; red/timeout/5xx retorna `{tipo:'conexion', reintentable:true, mensaje:"Error de conexión con el servidor"}`; éxito 2xx retorna JSON/null; cuerpo vacío/no JSON no lanza.

## Fase 3 — Componentes base reutilizables

- [x] **T08 — Implementar `components/Loading.jsx`** — RF-5 — Hecho cuando: renderiza `role="status"` + `aria-live="polite"` con texto por defecto "Cargando...", prop `mensaje` opcional, sin ocultar `<nav>`, test manual `npm run dev` muestra cargando uniforme.

- [x] **T09 — Implementar `components/EmptyState.jsx`** — RF-5 — Hecho cuando: renderiza "Sin datos disponibles" por defecto (prop `mensaje` opcional) diferenciado de loading/error, centrado en `main`, sin botón.

- [x] **T10 — Implementar `components/ErrorMessage.jsx` (dos variantes)** — RF-5 — Hecho cuando: `variante="conexion"` muestra "Error de conexión con el servidor" + botón `<button>Reintentar</button>` con `role="alert"` y `disabled` cuando `cargando`; `variante="validacion"` muestra mensaje específico o genérico "No se pudo completar la solicitud..." sin botón (401 incluido).

- [x] **T11 — Implementar `components/ConfigErrorBanner.jsx` (error global)** — RF-4 — Hecho cuando: `role="alert"` a nivel layout, mantiene `<nav>` visible, suprime `<Outlet>`, botón Reintentar deshabilitado durante `cargando` y re-ejecuta verificación sin `window.location.reload` preservando ruta/historial.

- [x] **T12 — Implementar `hooks/useApiStatus.js` (estado efímero por sección)** — RF-5, RNF-6 — Hecho cuando: expone `{estado:'idle'|'cargando'|'exito'|'vacio'|'error', error, reintentar}`, vive solo en memoria (sin localStorage), deshabilita concurrentes y se descarta al desmontar.

## Fase 4 — Páginas esqueleto y prioridad

- [x] **T13 — Implementar `pages/PlaceholderPage.jsx`** — RF-2 — Hecho cuando: para cada ruta de sección muestra "<Sección> — En construcción" en español con `nav` visible, reutilizando layout.

- [x] **T14 — Implementar `pages/NotFoundPage.jsx` (404)** — RF-2 — Hecho cuando: ruta `*` muestra mensaje 404 en español ("Página no encontrada") con `nav` visible y sin romper layout.

- [x] **T15 — Integrar prioridad error global sobre placeholder/404/estados** — RF-2, RF-4 — Hecho cuando: con banner global activo no se renderiza placeholder ni 404 ni loading/vacío de sección; fallo aislado por sección no escala a global.

## Fase 5 — Accesibilidad y consistencia

- [x] **T16 — Aplicar decisiones de accesibilidad y mensajes fijos** — RF-1, RNF-3, RNF-4 — Hecho cuando: verificación manual: `nav`/`header`/`main`/`button` reales, `aria-current` en activo, `aria-live` polite/assertive, `aria-busy`, `lang="es"`, foco `focus-visible` sin trampa, y solo los dos genéricos permitidos.

## Fase 6 — Tests y cierre

- [x] **T17 — Tests de unidad `src/api/client.js` con Vitest + fetch mockeado** — RF-3, RF-4, RF-5 — Hecho cuando: pruebas cubren env vacía/inválida, normalización barra, 4xx con/sin mensaje (incluido 401→validación), red/timeout/5xx→conexion, abort 10s, sin peticiones concurrentes duplicadas; `npm run test` verde para este archivo.

- [x] **T18 — Tests de componentes `Loading|EmptyState|ErrorMessage|ConfigErrorBanner`** — RF-5, RF-4 — Hecho cuando: Loading `role="status"`, ErrorMessage conexion con botón y `disabled` durante carga, validacion sin botón, EmptyState texto, Banner suprime outlet y mantiene nav; todo con `fetch` mockeado.

- [x] **T19 — Tests de layout y ruteo (`AppLayout`, `PlaceholderPage`, `NotFoundPage`, navegación teclado)** — RF-1, RF-2 — Hecho cuando: nav siempre visible con 4 enlaces, `aria-current` activo, `userEvent.tab()` alcanza enlaces y Reintentar, acceso directo `/productos`→placeholder y `/ruta-inexistente`→404, global prevalece sobre 404.

- [x] **T20 — Verificación final lint, formato y manual en navegador** — Todos los RF, RNF-1–6 — Hecho cuando: `npm run lint` sin errores, `npm run format` aplicado, `npm run test` 100% verde, `grep -r "fetch(" src/components src/layout src/pages src/hooks` vacío, sin localStorage/sessionStorage, y `npm run dev` contra backend local muestra navegación, placeholders, 404 y ambos niveles de error con Reintentar funcionando.
