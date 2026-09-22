# Plan 013 — Pantalla de Autenticación Frontend

> Constitución: `frontend/docs/constitution.md` principios 1-6 | Spec: `specs/013-frontend-autenticacion/spec.md` RF-1..RF-5 (versión corregida con Impacto sobre 005) | Convenciones: `frontend/AGENTS.md` | Reutiliza `specs/005-frontend-base/plan.md` §2-3 (cliente `src/api/client.js` centralizado) y `specs/011-autenticacion/plan.md` §3-4 (contrato `POST /api/v1/auth/login` y protección `Bearer` 8h)

## 1. Alineación con constitución y AGENTS — [Cubre RF-1..RF-5]

- Respeta `frontend/docs/constitution.md:1` stack mínimo React 18 + Vite + Tailwind + fetch nativo; sin Redux/Zustand/UI kit — RF-1..RF-5 se resuelven con `useState`/`Context` mínimo + `fetch`.
- Respeta `constitution.md:3` API aislada — todo HTTP en `src/api/`; `pages/Login.jsx` y `layout/` nunca hacen `fetch` directo; `011` contrato `POST /auth/login` se consume solo vía cliente centralizado extendido (RF-2, RF-4).
- Respeta `constitution.md:5` estado servidor no cacheado — token solo en memoria, sin `localStorage`/`sessionStorage` para ningún dato incluido sesión; RNF-4 volatilidad ya aceptada (RF-2, RF-3, RNF-1).
- Respeta `constitution.md:6` idioma español — mensajes `Campo requerido`, `Credenciales inválidas`, `Sesión expirada...`, `Sesión cerrada...`, `Error de conexión con el servidor` (RF-1, RF-2, RF-5, RNF-3).
- Respeta `frontend/AGENTS.md:20` centralización en `src/api/` (un archivo por recurso, ningún componente con `fetch`) y `AGENTS.md:26` env var `.env`.
- Hereda `005` `react-router-dom` v6 como única dependencia de ruteo ya aprobada (AGENTS §10); no se añade estado global externo (AGENTS §27).

> Verificación: `grep -r "fetch(" src/components src/pages src/layout` vacío; solo `src/api/` contiene `fetch`; `package.json` sin `redux`/`zustand`.

## 2. Estructura de componentes en `frontend/src/` — [Cubre RF-1, RF-3, RF-5]

Extiende `005:plan.md:2` sin duplicar `Loading`/`ErrorMessage`/`EmptyState`/`ConfigErrorBanner` ya existentes.

```
frontend/src/
├── api/
│   ├── client.js              # extendido: inyección Bearer + interceptor 401 (RF-4, RF-5) — existe en 005, se modifica
│   └── auth.js                # nuevo: función login(email,password) delega a client.js — RF-2
├── context/
│   └── AuthContext.jsx        # nuevo: estado sesión en memoria — RF-2, RF-3, RF-5
├── layout/
│   ├── AppLayout.jsx          # modificado: header con botón Cerrar sesión condicional — RF-5
│   └── Header.jsx             # extraído del layout: banner título + botón Cerrar sesión — RF-5
├── pages/
│   ├── Login.jsx              # nuevo: formulario email+contraseña — RF-1, RF-2
│   ├── PlaceholderPage.jsx    # existente 005 — sin cambios
│   └── NotFoundPage.jsx       # existente 005 — sin cambios
├── components/
│   ├── ProtectedRoute.jsx     # nuevo: guard de rutas protegidas — RF-3 (wrapper de 005)
│   └── (Loading, ErrorMessage, EmptyState ya en 005) — reutilizados
├── App.jsx                    # modificado: rutas protegidas anidadas bajo ProtectedRoute — RF-3
└── main.jsx                   # sin cambios (provee BrowserRouter + AuthProvider)
```

Responsabilidad por archivo — RF cubierto:

| Archivo | Acción | RF | Responsabilidad |
|---------|--------|----|-----------------|
| `src/api/client.js` | **Modificar** | RF-4, RF-5 | Único punto con `fetch`; lee `VITE_API_URL`, normaliza barra, añade `Authorization: Bearer` si hay token en memoria **excepto** para `POST /api/v1/auth/login`, e intercepta `401` para deslogueo global. No persiste token. |
| `src/api/auth.js` | **Crear** | RF-2 | Función `login({email,password})` que delega a `client.js` `POST /api/v1/auth/login` con email ya con `trim`; no añade `Bearer`. No guarda token (lo devuelve al contexto). |
| `src/context/AuthContext.jsx` | **Crear** | RF-2, RF-3, RF-5 | Estado volátil `token` (`null` inicial siempre), expone `token`, `login(newToken)`, `logout()`, `isAuthenticated`. Sin `localStorage`. Provee a `AppLayout`, `ProtectedRoute`, `client.js` (via getter). |
| `src/components/ProtectedRoute.jsx` | **Crear** | RF-3 | Guard: si `!isAuthenticated` → `Navigate to="/login" state={{from: location}} replace`; si autenticado y ruta es `/login` → `Navigate to="/productos"`. Orden: se evalúa antes que `NotFound`. |
| `src/pages/Login.jsx` | **Crear** | RF-1, RF-2 | Form email+password con `autocomplete`, validación local `Campo requerido`, botón deshabilitado + spinner, mensajes `401`/`422`/red según contrato `011`. Al éxito llama `login(token)` y redirige a `state.from` o `/productos`. |
| `src/layout/Header.jsx` | **Extraer/Modificar** | RF-5 | Muestra `Cerrar sesión` solo si `isAuthenticated`; al click llama `logout()` → redirige `/login` con mensaje efímero. Nunca se muestra en `/login`. |
| `App.jsx` | **Modificar** | RF-3 | Monta `AuthProvider` + `BrowserRouter` + `Routes`: `/login` público, resto bajo `<ProtectedRoute><AppLayout><Outlet>`. `/` redirige a `/productos`. `*` → `NotFoundPage` solo dentro de protegidas. |

> Principio `AGENTS.md:17` y `constitution.md:2` (un componente por archivo, PascalCase) respetado.

## 3. Diseño del estado de sesión — [Cubre RF-2, RF-3, RF-5]

**Elección:** `React Context` mínimo (`AuthContext` con `createContext` + `useState`) y no estado elevado en `App.jsx` con prop drilling.

- **Justificación:** Context es parte de React 18 sin dependencia externa, cumple `AGENTS.md:27` (“no añadir librerías de estado sin preguntar”). Evita `Redux/Zustand` prohibidos por `constitution.md:1`. Alternativa descartada: elevar `token` a `App.jsx` y pasarlo por props a `Header`, `ProtectedRoute` y `client.js` obligaría a prop drilling a través de 3 niveles y acopla `App.jsx` a toda la app; con Context el cliente y el guard consumen el token sin pasar props. Se descarta `localStorage`/`sessionStorage` por `RNF-1` y spec RF-2 (nunca persistir).
- **Forma del contexto (sin código, solo contrato):**
  - Estado: `token: string | null` inicial siempre `null` al cargar la app (sin efecto de restauración, RNF-4 volatilidad).
  - Expone: `token` (lectura), `isAuthenticated: boolean` (`!!token`), `login(token: string)` (guarda en memoria), `logout()` (limpia a `null`).
  - Proveedor `AuthProvider` envuelve `BrowserRouter` en `main.jsx` para que `ProtectedRoute` y `Header` lo consuman.
  - No expone `setToken` directo; solo `login`/`logout` desacoplan la mutación.
- **Inicialización:** al cargar la app no hay intento de leer persistencia; `token` nace `null` → cualquier `/productos|proveedores|movimientos|stock|ventas` redirige a `/login` por `ProtectedRoute`. Esto satisface `spec.md` RF-3 `F5` pierde sesión y vuelve a `login` recordando ruta.
- **Ciclo:** `Login.jsx` → `auth.js login()` → `client.js POST /auth/login` → éxito → `AuthContext login(token)` → `ProtectedRoute` pasa a `isAuthenticated=true` → redirección.

> RF-2 (guardado solo en memoria), RF-3 (guard consume `isAuthenticated`), RF-5 (`logout` limpia y redirige). RNF-1 y RNF-4 verificados por prueba de recarga: `F5` → `token` `null`.

## 4. Diseño del cliente API centralizado extendido — [Cubre RF-4, RF-5]

Extiende `005:plan.md:3` `src/api/client.js` que ya valida `VITE_API_URL`, normaliza barra, timeout 10s con `AbortController` y tipa errores `validacion` vs `conexion`.

**Extensión para auth:**

- **Lectura de token sin acoplamiento circular:** `client.js` no importa `AuthContext` directamente (evita ciclo). Expone función `setAuthTokenGetter(getter: () => string|null)` que `AuthContext` registra al montar (`useEffect` en provider). En cada `request()` el cliente llama `getToken()` para decidir si adjunta header. Alternativa descartada: importar contexto dentro de `client.js` causaría dependencia de React en capa API y rompería `constitution.md:3` (API aislada de UI).
- **Inyección de Bearer:**
  - Si `url` termina en `/api/v1/auth/login` (comparación exacta tras normalizar `base + ruta`), **nunca** adjuntar `Authorization`, incluso si `getToken()` devuelve un token previo (RF-4 criterio 3 y decisión 4d).
  - Si no es login y `getToken()` no es `null`, adjuntar `Authorization: Bearer <token>`; si es `null`, no adjuntar (el guard ya bloqueó, pero por defensa no se envía header vacío).
- **Interceptor de 401 global (decisión crítica 1):**
  - Tras `fetch`, si `response.status === 401` **y** la `url` **no** es `/api/v1/auth/login`, entonces: (1) llamar a `onUnauthorized` callback registrado por `AuthContext` (que hace `logout()` + `navigate("/login", {state: {from: locationEnElMomento401, mensaje: "Sesión expirada..."}})`) y (2) propagar el error como `{tipo: 'autenticacion', mensaje: "Sesión expirada, inicia sesión nuevamente", reintentable: false}` para que el componente no muestre además `ErrorMessage` de sección. La lógica vive **dentro de `client.js`**, nunca en `components/` ni `layout/` (decisión 4i, respeta `constitution.md:3`).
  - Si `401` es de `POST /auth/login`, **no** se dispara el interceptor; se propaga como error `validacion` normal con mensaje `Credenciales inválidas` para que `Login.jsx` lo muestre en el formulario (RF-2).
  - Para cualquier otro `4xx`/`5xx`/red/timeout se mantiene la tipificación ya existente de `005` (`validacion` sin Reintentar vs `conexion` con Reintentar) sin limpiar sesión.
- **Manejo de 422 estructurado (decisión 4h):** si `response.status===422` y `body.detail` es array (Pydantic), el cliente extrae `detail[0].msg` legible; si es string, lo devuelve tal cual. Esto permite a `Login.jsx` mostrar el mensaje específico sin inventar genérico.

> RF-4 (inyección `Bearer` centralizada, exclusión login, sin persistencia), RF-5 (401 global limpia y redirige, con exclusión), RNF-2 (consistencia con `005` para otros errores). Verificación `constitution.md:3`: solo `src/api/` hace `fetch`.

## 5. Diseño del guard de rutas protegidas — [Cubre RF-3]

**Componente `ProtectedRoute.jsx` (wrapper sobre `Outlet` de `react-router-dom` v6):**

- **Lectura:** consume `isAuthenticated` de `AuthContext`.
- **Sin token y ruta protegida:** `return <Navigate to="/login" state={{from: location}} replace />` donde `location` es `useLocation()` actual (ej. `/stock`). No intenta `fetch`; guarda la ruta intentada en `location.state.from` (state de React Router, no en URL query ni en `sessionStorage`). Esto cumple RF-3 memoria de ruta intentada y decisión 4 de spec.
- **Con token y ruta `/login`:** `return <Navigate to="/productos" replace />` (cambiar de cuenta requiere logout explícito primero, decisión 4a).
- **Con token y ruta inexistente:** como `ProtectedRoute` envuelve todas las rutas protegidas **antes** que `Route path="*"` (`NotFoundPage`), el orden es: `Request → ProtectedRoute (chequea token) → si no token → /login` sin evaluar si `*` existe. Si hay token, entra al layout y `*` muestra `404` normal de `005`. Esto satisface decisión 2 (guard primero).
- **Con token y ruta válida:** `return <Outlet />` renderiza `AppLayout` + `Header` + `main`.

**Estructura de rutas en `App.jsx`:**

```
/ → Navigate to="/productos" replace
/login → <Login /> (público, fuera de ProtectedRoute)
/ (ProtectedRoute) → <AppLayout><Outlet>
    /productos → <PlaceholderPage nombre="Productos">
    /proveedores → <PlaceholderPage nombre="Proveedores">
    /movimientos → <PlaceholderPage nombre="Movimientos">
    /stock → <PlaceholderPage nombre="Stock">
    /ventas → (futura)
    * → <NotFoundPage>
```

> RF-3 completo (protección, memoria ruta intentada, default `Productos`, `F5` → login, `/login` autenticado → `Productos`, guard antes que `404`). Verificación: acceso directo sin token a `/stock` → `/login`; con token → `200`.

## 6. Flujo de login en pseudocódigo — [Cubre RF-1, RF-2, RF-3]

```
en Login.jsx, estado local: email, password, error, cargando

alSubmit(form):
  // 1. validación local RF-1 (solo requerido)
  si email.trim() === "" o password === "":
    mostrar "Campo requerido" en cada campo vacío
    retornar sin llamar a API
  emailTrim = email.trim() // decisión 4f

  // 2. llamada
  setCargando(true) // deshabilita inputs + botón + muestra spinner, RF-1
  try:
    respuesta = await auth.login({email: emailTrim, password}) // → client.post("/api/v1/auth/login") sin Bearer
    // 3a. éxito RF-2
    AuthContext.login(respuesta.access_token) // guarda solo en memoria
    destino = location.state?.from?.pathname || "/productos" // RF-3 memoria
    navigate(destino, {replace: true})
  catch (error):
    si error.status === 401:
      mostrar "Credenciales inválidas" en formulario, permanecer en /login, no guardar token // RF-2, nunca dispara interceptor global
    si error.status === 422:
      si error.detail es array: mostrar detail[0].msg legible
      si es string: mostrar tal cual // decisión 4h
      // caso residual, no guardar token
    si error.tipo === 'conexion' (red/timeout >10s):
      mostrar "Error de conexión con el servidor" con botón Reintentar // RF-2 + RNF-2
      Reintentar reejecuta alSubmit, deshabilitado mientras cargando
  finally:
    setCargando(false) // re-habilita inputs y botón
```

> RF-1 (validación `Campo requerido`, deshabilitados, autocomplete), RF-2 (`trim`, sin `Bearer`, manejo `401`/`422`/red), RF-3 (redirección a ruta intentada o `Productos`), RNF-1 (solo memoria).

## 7. Flujo de logout y de expiración/401 global en pseudocódigo — [Cubre RF-5]

**Logout explícito (vive en `Header.jsx` + `AuthContext`):**

```
en Header.jsx, si isAuthenticated:
  mostrar botón "Cerrar sesión" siempre visible en header // RF-5, decisión 4j (Login nunca lo muestra)
  alClickCerrarSesion():
    AuthContext.logout() // limpia token a null, sin fetch
    navigate("/login", {state: {mensaje: "Sesión cerrada correctamente"}, replace: true})
    // Login muestra banner efímero 3 segundos con ese mensaje, mismo patrón 006-009 // decisión 4b

// No existe atajo para cambiar de cuenta sin logout (decisión 4a)
```

**Expiración/401 global (vive en `client.js` interceptor + `AuthContext`):**

```
en client.js request(ruta, opciones):
  headers = {}
  si ruta !== "/api/v1/auth/login" y getToken() !== null:
    headers.Authorization = "Bearer " + getToken() // RF-4
  respuesta = await fetch(base + ruta, {headers, signal: AbortController 10s})
  si respuesta.status === 401 y ruta !== "/api/v1/auth/login":
    // solo para peticiones con Bearer que fallan, nunca para login RF-5 vs RF-2
    AuthContext.logout() // limpia token
    // esta lógica está en client.js, no en componentes (decisión 4i)
    navigate("/login", {state: {from: locationActualAntesDel401, mensaje: "Sesión expirada, inicia sesión nuevamente"}, replace: true})
    // mensaje persiste hasta que usuario interactúe con formulario // decisión 4b
    lanzar error tipo 'autenticacion' para que el componente no pinte ErrorMessage de sección (prevalece redirección global RF-5)
  sino si status 401 y ruta === "/auth/login":
    propagar como error validacion 401 normal para Login.jsx // exclusión decisión 1
  sino si otro 4xx/5xx/red:
    propagar según tipificación existente de 005 sin limpiar token
```

> RF-5 completo (limpieza, redirección, mensajes persistente/efímero, prevalencia sobre error de sección, lógica en `client.js` no en layout).

## 8. Decisiones técnicas justificadas — [Cubre RF-3, RF-4, RF-5, RNF-1, RNF-4]

1.  **Mecanismo de guardado de ruta intentada: `state` de React Router vs query param `?next=` vs `sessionStorage`**
    - Elegida: `location.state.from` de `react-router-dom` (`Navigate state={{from: location}}`).
    - Descartada: query param `?next=/stock` (expone ruta en URL, requiere sanitización, ensucia historial) y `sessionStorage` (rompe RNF-1 “sin persistencia” y no sobrevive a `F5` de forma limpia, además requiere limpiar manual).
    - Motivo: `state` es volátil, no aparece en URL, se pierde correctamente tras `F5` (coherente con volatilidad de sesión) y es estándar en `react-router-dom` v6 usado ya en `005:plan.md:7`. No añade dependencia y respeta `constitution.md:5`.
2.  **Estado de sesión: `Context` mínimo vs estado elevado en `App.jsx` con prop drilling**
    - Elegida: `AuthContext` (`createContext` + `useState` + `useMemo`) con `login`/`logout`/`token`.
    - Descartada: elevar `token` a `App.jsx` y pasar por props a `Header`, `ProtectedRoute` y `client.js` (prop drilling, acopla `App.jsx`).
    - Motivo: Context es API nativa de React, no dependencia externa, cumple `AGENTS.md:27` y `constitution.md:1` (sin Redux/Zustand). Mantiene `client.js` desacoplado vía getter, testeable con `fetch` mockeado.
3.  **Interceptor de 401: extensión del `client.js` fetch existente de `005` vs `Axios` o middleware de router**
    - Elegida: envolver `request()` existente de `005` con chequeo `status===401` y exclusión `url.endsWith("/auth/login")`, llamando a `onUnauthorized` registrado por `AuthContext`.
    - Descartada: migrar a `Axios` con interceptores (añade dependencia, viola `constitution.md:1` stack mínimo) y descartada `middleware` de router que parsea `location.pathname` (duplica lógica de rutas, riesgo de dejar lock si se ejecuta tarde como en `011`).
    - Motivo: reutiliza `fetch` + `AbortController` 10s ya validado en `005`, mantiene “API aislada” y centraliza `401` en un solo lugar testeable.
4.  **Deshabilitado durante carga: botón + inputs vs solo botón**
    - Elegida: deshabilitar ambos inputs y botón con spinner (decisión 4e).
    - Descartada: solo botón. Motivo: evita edición concurrente mientras la petición está en vuelo, mismo patrón de `ConfigErrorBanner` de `005` que deshabilita Reintentar.
5.  **Trim de email antes de enviar vs enviar tal cual**
    - Elegida: `trim` en frontend antes de `POST /login` (decisión 4f).
    - Descartada: enviar con espacios. Motivo: `011` normaliza `trim+lower` en backend; hacer `trim` evita roundtrip innecesario por espacios accidentales y es coherente con `002` proveedores.
6.  **Autocompletado permitido**
    - Elegida: `autocomplete="email"` y `autocomplete="current-password"` (decisión 4g).
    - Descartada: `autocomplete="off"`. Motivo: no interfiere con seguridad de token en memoria y mejora UX de mostrador compartido; el navegador guarda credenciales, no token.

## 9. Estrategia de tests — [Cubre RF-1..RF-5, RNF-1..RNF-5, constitution.md:4]

Stack heredado de `005:plan.md:9` `Vitest` + `Testing Library` + `jsdom`, `fetch` mockeado (`vi.stubGlobal("fetch", ...)`) — sin escribir código aquí.

**`pages/Login.jsx` — pruebas de componente con `AuthContext` mockeado:**
- Renderiza formulario con `email`, `contraseña`, `Iniciar sesión`, sin botón `Cerrar sesión` y con `autocomplete` correcto (RF-1, RNF-5).
- Validación local: submit con campos vacíos → muestra `Campo requerido` sin llamar a `fetch` (RF-1).
- Submit con email no vacío y `trim` aplicado → `fetch` llamado con email ya con `trim`, sin `Authorization` header (RF-2, RF-4).
- Mientras `fetch` pendiente → inputs y botón `disabled` y spinner visible; segundo click ignorado (RF-1, Casos límite).
- `fetch` resuelve `401` → muestra `Credenciales inválidas`, permanece en `/login`, `login` no llamado (RF-2, exclusión).
- `fetch` resuelve `422` con `detail` array → muestra primer mensaje legible; con string → muestra tal cual (decisión 4h).
- `fetch` rechaza red/timeout → muestra `Error de conexión con el servidor` con `Reintentar` que reejecuta `fetch` (RF-2).

**`components/ProtectedRoute.jsx` — guard de rutas:**
- Sin token → `Navigate` a `/login` con `state.from` igual a `location` inicial, sin intentar `fetch` (RF-3, RF-4).
- Sin token y ruta inexistente `/ruta-inexistente` → va a `/login`, no a `404` (orden guard primero, decisión 2).
- Con token y `location` `/login` → `Navigate` a `/productos` (RF-3, decisión 4a).
- Con token y ruta válida → renderiza `Outlet`/`AppLayout`.
- `F5` simulado (re-mount con `token` null) → va a `/login` recordando `from` (RNF-4).

**`src/api/client.js` — interceptor 401:**
- `POST /auth/login` con token previo en memoria → `fetch` sin `Authorization` (RF-4).
- `GET /api/v1/productos` con token → `fetch` con `Bearer`; sin token → sin header (RF-4).
- `GET /productos` con token válido que devuelve `401` → llama `logout` del contexto, navega a `/login` con `Sesión expirada...`, no lanza `ErrorMessage` de sección (RF-5).
- `POST /auth/login` que devuelve `401` → **no** llama `logout` ni navega, solo propaga error `401` para `Login.jsx` (exclusión).
- Otros `4xx`/`5xx`/red → no limpia token ni navega, propaga tipificación existente de `005` (RF-5).

**`layout/Header.jsx` — botón condicional:**
- Sin token (en `/login`) → no renderiza `Cerrar sesión` (decisión 4j).
- Con token → renderiza `Cerrar sesión` siempre visible en header, click llama `logout`, navega a `/login` con `Sesión cerrada correctamente` efímero 3s (RF-5).
- Doble click rápido en `Cerrar sesión` → solo un `logout` (Caso límite).

> Constitución `frontend/docs/constitution.md:4` (cada componente con lógica prueba `loading/error/success` con `fetch` mockeado) y `AGENTS.md:20` (solo `src/api/` hace `fetch`) verificados por `grep` y `npm run test` verde.

## 10. Cobertura de RFs — trazabilidad

| Parte del plan | RF cubierto | Evidencia verificable | Reutiliza `005`/`011` |
|----------------|-------------|-----------------------|------------------------|
| `Login.jsx` form `Campo requerido` + `trim` + `autocomplete` + disabled | RF-1 | campos vacíos → no fetch, `trim` antes de `POST`, inputs deshabilitados | `005` validación forma |
| `auth.js` `POST /auth/login` sin `Bearer` | RF-2 | `fetch` sin `Authorization` incluso con token previo | `011` contrato |
| `Login.jsx` manejo `401`/`422`/red con mensajes y `Reintentar` | RF-2 | `Credenciales inválidas` tal cual, `422` primer mensaje, `Error de conexión` con Reintentar | `011` + `005` tipificación |
| `AuthContext` token solo en memoria `null` inicial | RF-2, RNF-1, RNF-4 | `F5` → `null`, sin `localStorage` | `005` RNF-6 |
| `ProtectedRoute` guard + `state.from` + orden antes de `*` | RF-3 | sin token → `/login` recordando `/stock`, con token `/login`→`/productos`, sin token + `*` → `/login` no `404` | `005` `react-router-dom` |
| `client.js` inyección `Bearer` excepto login + getter | RF-4 | `Authorization` solo con token y no en login | `005` cliente centralizado |
| `client.js` interceptor `401` con exclusión login + `AuthContext.logout` | RF-5 | `401` con Bearer → limpia + `/login` `Sesión expirada` persistente; `401` login → no limpia | `011` exp 8h |
| `Header.jsx` `Cerrar sesión` condicional + efímero 3s | RF-5 | visible solo autenticado, sin confirmación, sin `fetch`, mensaje 3s | `006-009` banner |
| Tests componente Login/guard/interceptor/header | RF-1..RF-5 | `npm run test` verde con `fetch` mockeado | `005` estrategia |

## 11. Fuera de alcance del plan (confirmado, `spec.md: Fuera de alcance`)

No se diseña registro, recuperación/reset, roles/permisos, `refresh`/rotación, persistencia/`recordarme`, rate limiting, i18n, tema oscuro, notificaciones, responsive móvil — tal como `spec.md`.

## 12. Dudas abiertas

Ninguna bloqueante. Quedan como `[NECESITA ACLARACIÓN]` en spec: `refresh` silencioso y rol en header si se añaden en futuro. Para múltiples pestañas, ya documentado en RNF-4 como limitación consciente (cada pestaña sesión independiente). Otros puntos QA (back del navegador tras logout, orden inicialización guard vs error global) quedan diferidos a implementación en este plan (guard con `state.from` y `client.js` interceptor) y no requieren spec adicional.
