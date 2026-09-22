# Plan 005 — Base / Esqueleto Frontend

## 1. Alineación con constitución y AGENTS

- Respeta `frontend/docs/constitution.md:3` stack mínimo (React 18 + Vite + Tailwind + fetch, sin estado global) — RF-1 a RF-5 se resuelven sin Redux/Zustand.
- Respeta `frontend/docs/constitution.md:5` API aislada — todo HTTP en `src/api/`; `spec.md:37-42` RF-3.
- Respeta `frontend/docs/constitution.md:7` estado servidor no cacheado — sin localStorage, revalidación por reintento (`spec.md:68` RNF-6).
- Respeta `frontend/docs/constitution.md:8` idioma español — mensajes genéricos fijos (`spec.md:65` RNF-3).
- Respeta `frontend/AGENTS.md:20` centralización en `src/api/` y `frontend/AGENTS.md:26` env var (`.env`).
- Única excepción a `frontend/AGENTS.md:27` "no añadir dependencias": se solicita aprobación para `react-router-dom` (ver §5) — RF-1/RF-2 sin él obligan a reinventar ruteo.

## 2. Estructura de carpetas y archivos en `frontend/src/` — [Cubre RF-1, RF-2, RF-3, RF-5]

```
frontend/src/
├── api/
│   ├── client.js        # cliente base centralizado (único punto con fetch) — RF-3, RF-4, RF-5
│   └── health.js        # (opcional) verificación de conectividad inicial para RF-4; si no, se usa client.js directo
├── components/
│   ├── Loading.jsx      # estado cargando uniforme — RF-5
│   ├── ErrorMessage.jsx # estado error por sección/conexión con Reintentar — RF-5
│   ├── EmptyState.jsx   # estado vacío — RF-5
│   └── ConfigErrorBanner.jsx # banner global configuración/conexión — RF-4
├── layout/
│   ├── AppLayout.jsx    # layout persistente: header + nav + main + outlet — RF-1, RF-4
│   └── NavLinkItem.jsx  # link con marcado activo — RF-1
├── pages/
│   ├── PlaceholderPage.jsx # placeholder "En construcción" con nombre de sección — RF-2
│   └── NotFoundPage.jsx    # 404 — RF-2
├── hooks/
│   └── useApiStatus.js  # hook efímero para estado cargando/error/vacío por sección — RF-5 (solo memoria, sin localStorage, RNF-6)
├── App.jsx              # definición de rutas y montaje de AppLayout — RF-1, RF-2
└── main.jsx             # punto de entrada Vite (ya existente)
```

Responsabilidad por carpeta:
- `api/`: única capa con `fetch`; valida y normaliza `VITE_API_URL`, expone función base y propaga errores tipados (validación vs conexión). Ningún componente/hook hace fetch directo.
- `components/`: presentacionales puros, sin llamadas HTTP, reutilizables por 006-009.
- `layout/`: navegación persistente y contenedor semántico; no contiene lógica de negocio.
- `pages/`: vistas vacías del esqueleto (no son CRUD); solo usan componentes base.
- `hooks/`: estado local efímero de memoria para una carga por sección (cargando/error/vacío) con reintento; se descarta al desmontar.

> Verificación constitución §3: `grep -r "fetch(" src/components src/layout src/pages src/hooks` debe quedar vacío; solo `src/api/` contiene fetch.

## 3. Diseño del cliente API centralizado — [Cubre RF-3, RF-4, RF-5]

**Lectura de `VITE_API_URL`:**
- Origen único: `import.meta.env.VITE_API_URL` leído solo en `src/api/client.js` al iniciar.
- Validación (RF-3): `trim()`; si ausente/vacía/solo espacios o no es URL absoluta con esquema `http://` o `https://` (validación con `URL` constructor) → no se intenta fetch, se marca estado `configInvalida` que RF-4 consume como error global. No hay fallback hardcodeado. `.env.example` documenta la variable (AGENTS §26).
- Normalización: se elimina barra final duplicada/faltante (`base.replace(/\/+$/,'')` conceptual) para que `base + "/api/v1/..."` nunca genere `//`.

**Forma del módulo base:**
- Exporta función `request(ruta, opciones)` y helper `get/post` delgados encima. No exporta la URL base directamente.
- Headers: `Content-Type: application/json` y `Accept: application/json` por defecto; deja pasar `headers` adicionales sin sobreescribir validación de negocio.
- Timeout: `AbortController` con 10s (RF-4/RF-5). Al superar, aborta y propaga como error de conexión; botón Reintentar queda habilitable tras abort.
- Parseo: intenta `response.json()`; si cuerpo vacío o no JSON, resuelve como `null` sin lanzar. Para 4xx, intenta extraer `mensaje`/`detail`/`error` del JSON; si no hay texto útil o no es español reconocible, el consumidor aplicará el genérico de validación según RF-5.

**Propagación de errores tipada (sin exponer stack técnico):**
- Error validación (4xx incluido 401): objeto `{ tipo: 'validacion', status: 4xx, mensaje: <texto API o genérico "No se pudo completar la solicitud...">, reintentable: false }`. No lleva botón Reintentar en UI.
- Error conexión (red, CORS, abort timeout, 5xx): `{ tipo: 'conexion', status: <5xx o null>, mensaje: "Error de conexión con el servidor", reintentable: true }`. Lleva botón Reintentar.
- Éxito 2xx: devuelve JSON parseado o null.

> RF-3: centralización y validación de env. RF-4: error global usa `tipo==='conexion'` + `configInvalida`. RF-5: componentes distinguen `tipo` para decidir mensaje y si muestran Reintentar.

## 4. Diseño de componentes base reutilizables — [Cubre RF-5]

Todos presentacionales, PascalCase (`frontend/AGENTS.md:15`), sin fetch, mensajes en español.

### 4.1 Loading — `components/Loading.jsx`
- Props: `mensaje?: string` (por defecto "Cargando..."), `ariaLive?: 'polite'` (por defecto).
- Render: contenedor con `role="status"` y `aria-live="polite"` + texto. No oculta `nav`.
- Ejemplo de uso: `<Loading mensaje="Cargando..." />` dentro de `main` de una sección mientras `useApiStatus` está en `cargando`.

### 4.2 ErrorMessage — `components/ErrorMessage.jsx`
- Props: `mensaje: string` (ya resuelto: genérico de conexión o específico 4xx o genérico validación), `onReintentar?: () => void`, `cargando?: boolean` (deshabilita botón durante petición), `variante: 'conexion' | 'validacion'` (determina si muestra botón).
- Render: `role="alert"` + `aria-live="assertive"` para error, botón `<button>` real con texto "Reintentar", `disabled` cuando `cargando=true`, `aria-busy` reflejado.
- Regla RF-5: `variante==='conexion'` → muestra botón; `variante==='validacion'` → no muestra botón (incluido 401).
- Ejemplo de uso: `<ErrorMessage mensaje="Error de conexión con el servidor" variante="conexion" onReintentar={recargar} cargando={cargando} />` vs `<ErrorMessage mensaje={mensajeApi} variante="validacion" />`.

### 4.3 EmptyState — `components/EmptyState.jsx`
- Props: `mensaje?: string` (por defecto "Sin datos disponibles"), `descripcion?: string` opcional.
- Render: bloque centrado en `main` con texto diferenciado de error/cargando, sin botón.
- Ejemplo de uso: `<EmptyState mensaje="Sin datos disponibles" />` cuando API devuelve lista vacía.

## 5. Diseño del layout y ruteo — [Cubre RF-1, RF-2]

**Componente navegación:**
- `layout/AppLayout.jsx` renderiza estructura semántica: `<header>` + `<nav aria-label="Navegación principal">` + `<main id="contenido-principal">` + área para banner global.
- `layout/NavLinkItem.jsx` envuelve cada enlace; usa `NavLink` de routing para aplicar clase activa + `aria-current="page"` cuando coincide ruta (RF-1 criterio 2 y RNF-4). Orden fijo: Productos, Proveedores, Movimientos, Stock. Foco visible con clases Tailwind `focus:ring`.
- Navegación siempre visible (RF-1, RF-2): `AppLayout` es padre de todas las rutas; `main` cambia vía `<Outlet>`.

**Ruteo — librería a usar:**
- **Elegida: `react-router-dom` v6 (BrowserRouter + Routes + NavLink + Outlet).**
  - Justificación: estándar de facto en React 18, API declarativa comprensible para junior (RNF-1), soporta `NavLink` con `isActive` y `aria-current` automático, 404 con `path="*"`, preserva historial/URL/parámetros sin recarga, maneja acceso directo por URL y refresh (requisito Casos límite). Una sola dependencia mínima, sin store global, compatible con Vite.
  - RF cubiertos: RF-1 (persistencia sin recarga, marcado activo, teclado), RF-2 (rutas `/productos`, `/proveedores`, `/movimientos`, `/stock` → `PlaceholderPage`; `*` → `NotFoundPage`; priorización RF-4 sobre ellas).
- **Alternativa descartada: ruteo manual con `useState` + `history.pushState` + `popstate`.**
  - Descartada porque: obliga a reimplementar parsing de URL, 404, preservación de query/scroll, accesibilidad de `aria-current` y foco, y manejo de refresh/acceso directo; aumenta complejidad para junior, viola RNF-1 y genera deuda para 006-009. También se descartó `wouter` (más ligero pero menor adopción/docs en español y sin ventaja real para 4 rutas) y `TanStack Router` (orientado a TypeScript y overkill para esqueleto MVP).

**Mapa de rutas (App.jsx):**
- `/` redirige a `/productos`.
- `/productos`, `/proveedores`, `/movimientos`, `/stock` → `PlaceholderPage` con prop `nombreSeccion`.
- `*` → `NotFoundPage` (404, mensaje en español).
- Todas anidadas bajo `AppLayout`; error global (RF-4) se renderiza dentro de `AppLayout` por encima de `<Outlet>` y, cuando activo, suprime el outlet.

> Verificación: `npm run test` debe cubrir que NavLink activo aplica `aria-current` y que navegación por teclado alcanza los 4 enlaces.

## 6. Manejo del banner de configuración faltante — [Cubre RF-4]

- Componente `components/ConfigErrorBanner.jsx` renderizado por `AppLayout` cuando `client.js` reporta `configInvalida` o la verificación inicial de conectividad falla (red/CORS/timeout 10s).
- Props: `mensaje` fijo "Error de conexión con el servidor", `onReintentar`, `cargando`.
- Comportamiento: `role="alert"` + `aria-live="assertive"` a nivel layout, mantiene `<nav>` visible, suprime `<Outlet>` (no muestra placeholder/404/cargando de sección). Botón "Reintentar" deshabilitado mientras `cargando`, al accionar re-ejecuta verificación sin `window.location.reload`, preservando ruta actual e historial; tras éxito, banner desaparece y se restaura la sección solicitada (Caso límite).
- Diferenciación: este banner solo para arranque/configuración; fallos posteriores por endpoint no lo activan, usan `ErrorMessage` por sección (RF-4 criterio 4).

## 7. Decisiones de accesibilidad concretas — [Cubre RF-1, RNF-4]

- Estructura semántica obligatoria: `<header>` para título app, `<nav aria-label="Navegación principal">` con `<ul><li>` para lista de enlaces, `<main id="contenido-principal">` para contenido, `<button>` reales para Reintentar (nunca `div` clicable).
- Atributos: `aria-current="page"` en enlace activo (NavLink), `aria-live="polite"` en Loading, `aria-live="assertive"` + `role="alert"`/`role="status"` en errores, `aria-busy` durante carga, `aria-label` en botón Reintentar si hay múltiples en pantalla, `htmlFor` + `id` en futuros inputs (preparado para 006-009, aunque 005 no tiene formularios).
- Foco: anillo visible `focus-visible:ring`, orden lógico header→nav→main, sin trampas de foco; banner global no roba foco de nav.
- Idioma: `lang="es"` en html, mensajes fijos en español.
- Alternativa descartada: usar `div` con `onClick` para navegación — descartada por no ser operable por teclado ni anunciable por lector.

## 8. Decisiones técnicas relevantes adicionales (con alternativa descartada)

1. **Fetch nativo vs Axios** — Elegido `fetch` + `AbortController`. Justificación: cumple `frontend/docs/constitution.md:3` sin añadir peso; suficiente con manejo tipado 4xx/5xx. Descartado Axios: añade dependencia, interceptores innecesarios para esqueleto, y obliga a mapear errores de forma distinta.
2. **JavaScript ES2022 sin TypeScript** — Elegido por `frontend/AGENTS.md:15` (sin TS en MVP) para mantener mantenibilidad junior. Descartado TypeScript: introduce barrera de aprendizaje y tooling extra sin beneficio para 4 rutas vacías.
3. **Tailwind mínimo vs CSS modules / UI kit** — Elegido Tailwind utilitario mínimo para anillo de foco y layout desktop-first. Descartado UI kit (Chakra/Material): viola constitución §1 (prohibido sin aprobación) y añade peso/branding prematuro (Fuera de alcance).
4. **Estado local con `useState`/`useEffect` + `useApiStatus` vs estado global** — Elegido estado efímero en memoria por sección (hook). Justificación: constitución §5 y RNF-6 prohíben persistencia; no se cachea inventario. Descartado Redux/Zustand/Context global: viola §1 y añade complejidad para banner que solo necesita prop drilling local.
5. **Timeout con AbortController (10s) vs `Promise.race` manual** — Elegido AbortController nativo, estándar y cancelable. Descartado `setTimeout` + race: no cancela el fetch subyacente, deja peticiones colgadas.

## 9. Estrategia de tests — [Cubre RF-1 a RF-5, RNFs, Constitución §4]

Stack: `Vitest` + `Testing Library` (`@testing-library/react`, `@testing-library/user-event`) + `jsdom`. Sin escribir código de tests en este plan, se define qué se prueba:

**Cliente API (`src/api/client.js`) — pruebas de unidad con fetch mockeado:**
- Lee solo `import.meta.env.VITE_API_URL` y no hardcodea (RF-3).
- Rechaza vacía/espacios/URL no http/https como `configInvalida` (RF-3/RF-4).
- Normaliza barra final (evita `//`).
- Propaga 4xx con mensaje API preservado y `reintentable:false` (incluido 401) y sin Reintentar; si cuerpo ausente/no JSON/no español, aplica genérico validación.
- Propaga red/timeout 10s/CORS/5xx como `tipo conexion` con genérico "Error de conexión..." y `reintentable:true`.
- Abort tras 10s cancela y no deja promise colgada; múltiples llamadas concurrentes a `request` no comparten AbortController.
- Verificación constitución §3: ningún test importa fetch fuera de `src/api/`.

**Componentes base:**
- `Loading`: renderiza "Cargando..." con `role="status"` y `aria-live="polite"`; sustituye contenido sin ocultar nav (RF-5).
- `ErrorMessage` variante conexion: muestra mensaje genérico + botón Reintentar habilitado, `role="alert"`, click llama `onReintentar`, deshabilitado cuando `cargando=true` evita duplicados (Caso límite).
- `ErrorMessage` variante validacion: muestra mensaje específico o genérico validación, sin botón (RF-5).
- `EmptyState`: muestra "Sin datos disponibles" diferenciado de loading/error.
- `ConfigErrorBanner`: cuando `configInvalida` o fallo inicial, muestra banner global con Reintentar, mantiene nav, suprime outlet, prioriza sobre placeholder/404 (RF-4).

**Layout y ruteo:**
- `AppLayout`: nav siempre visible con 4 enlaces, con `aria-label`, y enlace activo con `aria-current="page"` (RF-1).
- Navegación por teclado: `userEvent.tab()` alcanza los 4 enlaces y botón Reintentar sin trampa (RF-1/Caso límite).
- `PlaceholderPage`: para cada una de las 4 rutas muestra "<Sección> — En construcción" + nav visible (RF-2).
- `NotFoundPage`: ruta `*` muestra 404 en español + nav visible (RF-2).
- Prioridad: con banner global activo, placeholder/404 no se renderizan (RF-2 criterio 4).
- Desktop-first y semántica: `nav`, `main`, `header`, `button` reales presentes.

> Criterio finalización `spec.md:100`: `npm run test` verde y `npm run lint` sin errores; toda prueba mockea `fetch` global, no toca red real.

## 10. Cobertura de RFs — trazabilidad

| Parte del plan | RF cubierto | Evidencia verificable |
|---|---|---|
| Layout + NavLink + AppLayout + react-router-dom | RF-1 | nav persistente, `aria-current`, foco teclado, sin recarga |
| PlaceholderPage + NotFoundPage + priorización banner | RF-2 | 4 placeholders con nombre, 404 `*`, global prevalece |
| `src/api/client.js` con env var + validación + normalización + exclusividad fetch | RF-3 | `import.meta.env.VITE_API_URL` único, sin hardcode, grep vacío fuera de api |
| ConfigErrorBanner + verificación inicial 10s + Reintentar sin reload | RF-4 | error global layout, preserva ruta/historial, deshabilita concurrentes |
| Loading + ErrorMessage (conexion/validacion) + EmptyState + useApiStatus | RF-5 | dos niveles error, mensajes genéricos fijos, Reintentar solo conexion, sin duplicados |
| Estructura carpetas + hooks memoria + sin localStorage | RNF-6 / Const §5 | estado solo memoria |
| Tests Vitest + a11y + idioma | RNF-3, RNF-4, Const §4/§6 | español, semántica, `npm run test` verde |

## 11. Fuera de alcance del plan (confirmado)

No se diseña CRUD, tablas, paginación, filtros, formularios de 006-009, ni i18n, tema oscuro, toasts, auth, localStorage o responsive móvil — tal como `spec.md:84-91`.

## 12. Dudas abiertas

Ninguna bloqueante. Única aprobación requerida: añadir `react-router-dom` como dependencia justificada para RF-1/RF-2 (excepción a AGENTS §27). Si se rechaza, el plan alternativo es ruteo manual descartado arriba con impacto en mantenibilidad junior.
