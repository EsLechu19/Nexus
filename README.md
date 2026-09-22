# Nexus — Sistema de Gestión de Inventario para Tienda de Videojuegos

> Proyecto completo construido con **Spec-Driven Development (SDD)**. Backend FastAPI + PostgreSQL y Frontend React. Gestión de productos, proveedores, movimientos de stock y ventas con autenticación JWT y trazabilidad append-only.

---

## Índice

1. [Visión general](#visión-general)
2. [Arquitectura y Stack](#arquitectura-y-stack)
3. [Constitución del proyecto](#constitución-del-proyecto)
4. [Funcionalidades por Spec](#funcionalidades-por-spec)
5. [Modelo de datos](#modelo-de-datos)
6. [API REST](#api-rest)
7. [Frontend](#frontend)
8. [Autenticación](#autenticación)
9. [Instalación y ejecución](#instalación-y-ejecución)
10. [Credenciales de prueba](#credenciales-de-prueba)
11. [Testing, Lint y Tipado](#testing-lint-y-tipado)
12. [Flujo SDD utilizado](#flujo-sdd-utilizado)
13. [Estructura del repositorio](#estructura-del-repositorio)
14. [Estado actual y próximos pasos](#estado-actual-y-próximos-pasos)

---

## Visión general

**Nexus** es el sistema interno de una tienda de videojuegos para controlar inventario físico. Centraliza:

- **Catálogo** de productos (juegos, consolas, accesorios) con stock mínimo y estado activo/inactivo.
- **Proveedores** con validación de email y código único.
- **Movimientos de inventario** (entradas/salidas/entrada inicial) con cálculo de `stock_actual = stock_inicial + entradas − salidas`.
- **Consulta de stock** global y por producto con alerta `Bajo stock` cuando `0 < stock_minimo` y `stock_actual < stock_minimo`.
- **Ventas** atómicas multi-producto que generan `N` movimientos de salida vía `003` con `SELECT FOR UPDATE`, sin dejar stock parcial.
- **Autenticación** transversal: todo endpoint de negocio exige `Bearer <JWT>` (8h, `sub=email`), sin roles en MVP.

Todo el código, los tests y las migraciones se generaron siguiendo SDD: cada funcionalidad partió de una `spec.md` en notación EARS, pasó por clarificación QA, `plan.md`, `tasks.md` y solo entonces se implementó con TDD.

## Arquitectura y Stack

### Backend — `Nexus/`

| Capa | Responsabilidad | Principio |
|------|-----------------|-----------|
| `routers/` | Solo HTTP + validación Pydantic, delega a `services/` | Constitución §3 |
| `services/` | Lógica de negocio, cálculo de stock, orquestación de ventas | AGENTS §29 |
| `models/` | Entidades SQLAlchemy singular (`Producto`, `Proveedor`) → tablas plural | AGENTS §20 |
| `schemas/` | Schemas Pydantic de entrada/salida, nunca expone modelos | AGENTS §22 |
| `app/main.py` + `database.py` | FastAPI, CORS, `Base`, `get_db` | — |
| `alembic/` | Migraciones versionadas, nunca editar una ya aplicada | Constitución §5 |

**Stack:** `FastAPI` + `PostgreSQL` (SQLite `nexus.db` en dev) + `SQLAlchemy` + `Alembic` + `Pydantic` + `PyJWT` + `passlib[bcrypt]` + `python-multipart`. Python 3.11+ con `type hints` obligatorios.

### Frontend — `Nexus/frontend/`

`React 18` + `Vite` + `Tailwind CSS` + `fetch` nativo + `react-router-dom` v6 (única dependencia extra aprobada). Sin Redux/Zustand/UI kit, sin TypeScript en MVP, sin persistencia en cliente.

| Capa | Ubicación | Rol |
|------|-----------|-----|
| `src/api/` | `client.js`, `auth.js`, `productos.js`, `proveedores.js`, `movimientos.js`, `stock.js` | Único lugar con `fetch`, valida `VITE_API_URL`, inyecta `Bearer`, intercepta `401` |
| `src/context/` | `AuthContext.jsx` | Token solo en memoria (`null` inicial), `login`/`logout`/`isAuthenticated` |
| `src/components/` | `ProtectedRoute.jsx`, `Loading.jsx`, `ErrorMessage.jsx`, `EmptyState.jsx` | Guard y estados uniformes |
| `src/layout/` | `AppLayout.jsx`, `Header.jsx`, `NavLinkItem.jsx` | Layout persistente con nav y botón `Cerrar sesión` condicional |
| `src/pages/` | `Login.jsx`, `Productos.jsx`, `Proveedores.jsx`, `Movimientos.jsx`, `Stock.jsx` | Pantallas de negocio |
| `src/hooks/` | `useProductos.js`, `useProveedores.js`, `useMovimientos.js`, `useStock.js`, `useApiStatus.js` | Estado efímero en memoria, revalidación tras mutación |

Comunicación `frontend/docs/constitution.md:5`: estado solo en memoria, todo dato se revalida contra la API tras `POST/PATCH/DELETE`.

## Constitución del proyecto

Definida en `docs/constitution.md` (backend) y `frontend/docs/constitution.md`:

1. **Stack y Arquitectura** — solo stack aprobado, código en capas estrictas.
2. **Spec manda sobre código** — nada sin `spec.md` activa; PR enlaza spec.
3. **Lógica separada de Interfaz** — routers solo HTTP, services solo negocio.
4. **Tests obligatorios** — `pytest -v` / `npm run test` 100% verde antes de merge.
5. **Integridad Append-Only** — movimientos y ventas nunca se borran/modifican; esquema solo vía Alembic.
6. **Idioma** — código/comentarios y mensajes UI en español; identificadores en inglés (dominio en español permitido).

Verificación en cada tarea: `ruff check .`, `ruff format .`, `mypy app`, `alembic upgrade head`, Swagger en `/docs`.

## Funcionalidades por Spec

| Spec | Título | Qué entrega | RF principales |
|------|--------|-------------|----------------|
| **001** | Productos Catálogo | CRUD de catálogo con `sku` único `^[A-Z0-9_-]{3,20}$` normalizado `trim+upper`, `nombre` 2-100, `categoria` `videojuego|consola|accesorio`, `stock_inicial`/`stock_minimo` 0..1M, `estado` activo/inactivo, baja lógica. | RF-1..5 |
| **002** | Proveedores | CRUD de proveedores `codigo` único, `nombre` 2-100, `email` `local@dominio.tld` TLD≥2 ≤254 `trim+lower`, `telefono` opcional. | RF-1..5 |
| **003** | Movimientos Inventario | `POST /movimientos/entradas` y `/salidas` con `producto_codigo` + `cantidad` 1..1M `StrictInt` + `proveedor_codigo` (solo entradas) + `motivo` 2-200, `SELECT FOR UPDATE` para serializar, `GET /movimientos` historial filtrable. Append-only. | RF-1..3 |
| **004** | Consulta Stock | Derivación `stock_actual` y flag `alerta = stock_minimo>0 && stock_actual<stock_minimo` ( `<` estricto, `0` nunca alerta). `GET /stock` global orden `codigo ASC` y `GET /stock/{codigo}`. `stock_actual` nunca negativo. | RF-1..4 |
| **005** | Frontend Base | Esqueleto: `AppLayout` con nav persistente 4 secciones, `client.js` centralizado con `VITE_API_URL` validada y normalizada, timeout 10s, tipificación `validacion` vs `conexion`, `Loading`/`ErrorMessage`/`EmptyState`/`ConfigErrorBanner`, `react-router-dom` con `404` y priorización de error global. | RF-1..5 |
| **006** | Frontend Productos | `Productos.jsx` tabla 4 cols, `ProductoFormModal` (alta/edición) y `ProductoBajaDialog` (baja), revalidación tras mutación, manejo `4xx` sin Reintentar vs `5xx` con Reintentar, banner éxito `Producto creado correctamente` 3s. | 006 RF-1..5 |
| **007** | Frontend Proveedores | Análogo a productos, 5 cols, validación email `trim+lower`, unicidad. | 007 RF-1..5 |
| **008** | Frontend Movimientos | `MovimientosHistorial` 7 cols + `MovimientoFormModal` con alta entrada/salida, validación `cantidad` `StrictInt` y `motivo`, revalidación. | 008 RF-1..4 |
| **009** | Frontend Stock | `StockTabla` 5 cols `codigo|nombre|stock_actual|stock_minimo|alerta` con badge `Bajo stock` + fila coloreada, `alerta` leída del backend nunca recalculada, `stock_minimo null→0` mostrado como `0`. | 009 RF-1..2 |
| **010** | Frontend Diseño | Sistema de diseño retroactivo: paleta gamer sobria, tipografía `Inter`, escala 4px, botones primario/secundario/peligro, tablas/inputs/modales/badges uniformes, corrección de purga Tailwind en build. Sin cambios funcionales. | RF-1..6 |
| **011** | Autenticación Backend | `POST /api/v1/auth/login` público con `email`/`password` → `JWT HS256` `sub=email, exp=+8h` `bearer`; `get_current_user` valida `Authorization: Bearer` **antes** de BD/lock; todos `/api/v1/productos|proveedores|movimientos|stock` protegidos; `GET /docs` público pero `Try it out` protegido; modelo `usuarios` solo `email` único + `password_hash` bcrypt; creación solo vía `app/cli/crear_usuario.py`. | RF-1..5 |
| **012** | Ventas Backend | `POST /api/v1/ventas` 1-20 items con `producto_codigo` normalizado, `cantidad StrictInt`, `precio_unitario Decimal(12,2)` 0..1M, `SKU` duplicado→422, `total/subtotal` ignorados y recalculados `Decimal`, `cliente` embebido `nombre` 2-100 `email` opcional `002`; tablas `ventas` + `venta_items` con `movimiento_id FK UNIQUE`; transacción atómica: valida `422`→`404`→`400` con `SELECT FOR UPDATE`, luego `N` × `registrar_salida` de `003`; `GET /ventas` y `GET /ventas/{id}` protegidos, orden `created_at DESC, id DESC`, `movimientos_ids` trazables en `GET /movimientos`. | RF-1..4 |
| **013** | Frontend Autenticación | `Login.jsx` con `email`/`password` + `Campo requerido` local, `trim` email, `autocomplete`, botón deshabilitado con `Cargando...`; `AuthContext` token solo en memoria `null` inicial; `client.js` inyecta `Bearer` excepto `/auth/login` e intercepta `401` no-login → `logout` + `Sesión expirada`; `ProtectedRoute` guarda `state.from` y `guard` antes que `404`; `Header` con `Cerrar sesión` solo si autenticado → `Sesión cerrada correctamente` efímero 3s; `F5` pierde sesión y vuelve a `login` recordando ruta. | RF-1..5 |

Cada spec siguió: `spec.md` (EARS) → clarificación QA → `plan.md` → `tasks.md` (T01..Tn, 20-30 min, `Hecho cuando:` verificable) → implementación TDD (test primero) → validación RF por RF.

## Modelo de datos

**PostgreSQL (SQLite dev). Tablas en plural, modelos en singular.**

- `usuarios` — `id PK`, `email VARCHAR(254) UNIQUE` (normalizado `trim+lower`), `password_hash VARCHAR(72)` bcrypt, `created_at TIMESTAMPTZ` — migración `ff5b41c7a385`.
- `productos` — `sku VARCHAR(20) UNIQUE` `CHECK 3..20`, `nombre VARCHAR(100)` `CHECK trim 2..100`, `categoria` `videojuego|consola|accesorio`, `stock_inicial/minimo INT 0..1M`, `estado` `activo|inactivo`, `created_at/updated_at` — migración `63276eeea69c`.
- `proveedores` — `codigo VARCHAR(20) UNIQUE`, `nombre`, `email VARCHAR(254)`, `telefono` opcional — migración `37840112ca70`.
- `movimientos_inventario` — `id PK`, `producto_id FK RESTRICT`, `proveedor_id FK RESTRICT NULL` (solo entradas), `tipo` `entrada|salida|entrada_inicial`, `cantidad INT 1..1M`, `motivo VARCHAR(200)`, `created_at` — migración `9111dba96a53`.
- `ventas` — `id PK`, `created_at TIMESTAMPTZ DEFAULT now()`, `cliente_nombre VARCHAR(100) CHECK 2..100`, `cliente_email VARCHAR(254) NULL`, `total NUMERIC(12,2)` — migración `2c3245f4f658`.
- `venta_items` — `id PK`, `venta_id FK ventas RESTRICT`, `producto_id FK productos RESTRICT`, `cantidad INT`, `precio_unitario NUMERIC(12,2)`, `subtotal NUMERIC(12,2)`, `movimiento_id FK movimientos_inventario UNIQUE RESTRICT` + índices `ix_ventas_created_at`, `ix_venta_items_venta_id`.

Append-only: nunca `UPDATE/DELETE` sobre `movimientos_inventario` ni `ventas`.

## API REST

Base `http://localhost:8000` (`VITE_API_URL`). Prefijo `/api/v1`. JSON `application/json`. Mensajes en español.

### Públicos

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/v1/auth/login` | `{"email","password"}` → `{"access_token","token_type":"bearer"}` 8h. `422` si faltan campos, `401 Credenciales inválidas` genérico para resto. |
| `GET` | `/docs`, `/openapi.json` | Swagger, sin token para visualización; `Try it out` sin `Authorize` → `401`. |

### Protegidos — requieren `Authorization: Bearer <token>` validado **antes** de BD/lock. Sin token/inválido/expirado → `401`.

| Recurso | Endpoints | Notas |
|---------|-----------|-------|
| **Productos** | `POST /productos` 201, `GET /productos` 200 list activos, `GET /productos/{sku}` 200, `PATCH /productos/{sku}` 200, `DELETE /productos/{sku}` baja lógica | `sku` normalizado `trim+upper`, unicidad case-insensitive |
| **Proveedores** | `POST /proveedores` 201, `GET /proveedores` 200, `GET /proveedores/{codigo}` 200, `PATCH /{codigo}` 200, `DELETE /{codigo}` 200 | `email` validación `002` |
| **Movimientos** | `POST /movimientos/entradas` 201, `POST /movimientos/salidas` 201, `GET /movimientos?producto_codigo=&tipo=` 200 | `cantidad` `StrictInt`, `motivo` 2-200, `SELECT FOR UPDATE` |
| **Stock** | `GET /stock` 200 global `codigo ASC` con `alerta`, `GET /stock/{codigo}` 200 o `404` si inactivo/inexistente | `stock_actual` derivado, nunca negativo |
| **Ventas** | `POST /ventas` 201 con `cliente{nombre,email?}` + `items[1..20]` → `id, created_at Z, cliente, items{subtotal}, total, movimientos_ids`, `GET /ventas` 200 `[]` o lista `created_at DESC, id DESC`, `GET /ventas/{id}` 200 o `404` | `total`/`subtotal` ignorados si se envían, `SKU` duplicado tras normalización → `422`, `404` no existe, `400` inactivo/stock `disponible/solicitado`, atómico `BEGIN/COMMIT` |

Códigos transversales: `422` validación estructura, `404` no encontrado, `400` inactivo/stock, `401` sin `Bearer`, `5xx`/red/timeout 10s → `Error de conexión con el servidor` con `Reintentar` en frontend.

## Frontend

**Stack:** `React 18` + `Vite` + `Tailwind 3.4` + `fetch` + `react-router-dom 6.23` + `Vitest` + `Testing Library`.

**Rutas:**

- `/login` — pública, fuera de `ProtectedRoute`. Si ya autenticado → `Navigate to="/productos"`. Muestra `Sesión expirada...` persistente hasta interacción o `Sesión cerrada correctamente` efímero 3s.
- Protegidas bajo `<ProtectedRoute><AppLayout>` — `/productos`, `/proveedores`, `/movimientos`, `/stock`, `/ventas` (futura), `/` → `/productos`, `*` → `NotFoundPage` (404). Guard: sin token → `<Navigate to="/login" state={{from: location}} replace />` sin `fetch`, recordando ruta; con token + `*` → `404`; `F5` pierde token (memoria) y vuelve a `/login` recordando ruta.

**Layout `AppLayout`:** `Header` (`Nexus — Gestión de Inventario` + `Cerrar sesión` solo si `isAuthenticated`), `nav` con 4 links con `aria-current="page"` y `focus-visible:ring`, `main#contenido-principal` con `<Outlet />`, `ConfigErrorBanner` global si `VITE_API_URL` inválida o API caída al iniciar.

**Estados uniformes (`005`):** `Loading` (`Cargando...` `role="status"`), `ErrorMessage` (`validacion` sin `Reintentar` vs `conexion` con `Reintentar` `disabled` mientras carga), `EmptyState` (`Sin datos disponibles`).

## Autenticación

### Backend (`011`)

- **Modelo:** solo `email` + `password_hash` bcrypt cost 12, `email` único tras `normalizar_email()` (`trim+lower`, regex `002`).
- **JWT:** `HS256` con `JWT_SECRET_KEY` (≥32 bytes, vía `.env` nunca commiteado), `sub=email`, `exp=now+8h`, sin roles, stateless, sin revocación (limitación aceptada `RNF-8`: token de usuario borrado sigue válido hasta `exp`).
- **CLI:** `python -m app.cli.crear_usuario --email <email> --password <password>` — valida email `002` y `password ≥8`, hashea y hace `INSERT`; duplicado → `Email ya existe`.
- **Protección:** `app/services/deps.py:get_current_user` lee `Authorization` `Bearer ` case-sensitive, verifica firma/`exp` vía `PyJWT` **antes** de abrir `Session`/`SELECT FOR UPDATE`.

### Frontend (`013`)

- **Estado:** `src/context/AuthContext.jsx` — `token: string|null` inicial `null`, `isAuthenticated`, `login(token)`, `logout()`; nunca `localStorage`/`sessionStorage`; `F5` → `null` (RNF-4 volatilidad consciente, cada pestaña sesión independiente).
- **Cliente:** `src/api/client.js` expone `setAuthTokenGetter(() => token)` y `setOnUnauthorized` registrados por `AuthContext` vía `useEffect`; inyecta `Bearer` en cada `fetch` excepto `POST /api/v1/auth/login`; intercepta `401` no-login con token → `logout()` + `navigate("/login", {state: {mensaje: "Sesión expirada..."}})`, `401` de login se propaga como `validacion` con `Credenciales inválidas`.
- **Login:** `src/pages/Login.jsx` — `autocomplete="email"/"current-password"`, validación local solo `Campo requerido` si vacío tras `trim` (formato delegado a backend), `trim` email antes de `loginApi`, `fetch` sin `Bearer`, `disabled` inputs+botón con `Cargando...` e ignora dobles clics vía `useRef`, `401`→`Credenciales inválidas`, `422` array→primer `msg` legible, red/timeout→`Error de conexión` con `Reintentar`, éxito→`login(access_token)` y `navigate(state.from || "/productos")`, nunca muestra registro/recuperación/roles.
- **Header:** `src/layout/Header.jsx` — `Cerrar sesión` siempre visible en header solo si `isAuthenticated` (nunca en `/login`), sin `fetch`, sin confirmación, `logout()` + `navigate("/login", {state: {mensaje: "Sesión cerrada correctamente"}})` efímero 3s, doble click ignorado.

## Instalación y ejecución

### Requisitos

- Python 3.11+, Node 18+, PostgreSQL (o SQLite dev `nexus.db`), `uvicorn`, `npm`.

### Backend

```powershell
cd Nexus
pip install -r requirements.txt
# JWT (mínimo 32 bytes, nunca hardcodeado)
$env:JWT_SECRET_KEY="dev-secret-32chars-minimo-para-jwt!!"
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# Swagger en http://localhost:8000/docs
```

Crear usuario (fuera de API):

```powershell
python -m app.cli.crear_usuario --email "admin@nexus.com" --password "NexusAdmin123"
# Ya existen para pruebas: admin@tienda.com / Admin1234  y  demo@tienda.com / Demo12345
```

### Frontend

```powershell
cd Nexus/frontend
npm install
# .env ya contiene VITE_API_URL=http://localhost:8000 (sin barra final)
npm run dev      # http://localhost:5173
npm run build    # build producción
```

`VITE_API_URL` debe ser `http(s)://` absoluta; vacía/espacios/no-absoluta → `ConfigErrorBanner` `Error de conexión con el servidor` con `Reintentar`.

## Credenciales de prueba

Creadas vía CLI y verificadas con `POST /api/v1/auth/login` → `200`:

| Email | Contraseña | Uso |
|-------|------------|-----|
| `admin@nexus.com` | `NexusAdmin123` | Usuario de prueba solicitado (creado ahora) |
| `admin@tienda.com` | `Admin1234` | Admin principal (recreado) |
| `demo@tienda.com` | `Demo12345` | Demo secundario |

Login en `http://localhost:5173/login` con cualquiera de ellas. Tras `F5` o cierre de pestaña el token se pierde (memoria) y se vuelve a `/login` recordando la ruta (ej. `/stock`).

## Testing, Lint y Tipado

**Backend (`Nexus/`):**

```powershell
pytest -v                          # 469 tests (001-004 con Bearer + 011-012)
pytest --cov=app --cov-report=term-missing
ruff check .                       # All checks passed
ruff format --check .              # 121 files already formatted
mypy app --ignore-missing-imports  # Success in 34 files
alembic current                    # 2c3245f4f658 (head) — ventas
alembic downgrade -1; alembic upgrade head # sin pérdida
```

**Frontend (`Nexus/frontend/`):**

```powershell
npm run test   # 40 files 322 tests (Vitest + Testing Library, fetch mockeado)
# cubre: Login (8), ProtectedRoute (6), client Bearer/interceptor (6), Header (6),
# AuthContext (6), auth wrapper (5), AppLayout, a11y, productos/proveedores/movimientos/stock, design tokens
npm run lint   # echo (sin errores, T20)
```

Verificación manual tras cada tarea: `npm run dev` contra backend real en `localhost:8000`, `Bearer` visible en `movimientos`/`stock`/`ventas`, `401` expirado → `Sesión expirada`, `F5` → `login`.

## Flujo SDD utilizado

```
Constitución → Spec (EARS) → Clarificación QA → Plan → Tasks (T01..Tn, 20-30 min, Hecho cuando: verificable) → Implementación TDD (test primero, una tarea cada vez, PÁRATE) → Validación RF por RF → Cambio (primero spec, luego código)
```

Artefactos por spec en `specs/00X-nombre/`:
`spec.md` (contexto, usuarios, HU, RF con EARS, RNF, casos límite, fuera de alcance, criterios, dudas `[NECESITA ACLARACIÓN]`) → `plan.md` (módulos, modelo, contrato API, decisiones con alternativa descartada, estrategia tests) → `tasks.md` (checkboxes) → `app/`+`frontend/src/`+`tests/` → validación.

Plantillas y pizarra del curso en `samples/` y `sdd.excalidraw`.

## Estructura del repositorio

```
hello-sdd/
├── samples/                    # Plantillas del curso SDD (AGENTS, spec, prompts, pizarra)
├── habits-cli/                 # Proyecto de ejemplo del curso (CLI hábitos, no Nexus)
└── Nexus/                      # Proyecto principal — Sistema de Gestión de Inventario
    ├── AGENTS.md               # Instrucciones backend (comandos, estilo, reglas, verificación)
    ├── docs/constitution.md    # 6 principios innegociables backend
    ├── frontend/
    │   ├── AGENTS.md           # Instrucciones frontend
    │   ├── docs/constitution.md # 6 principios frontend (stack mínimo, API aislada, sin persistencia)
    │   ├── src/
    │   │   ├── api/            # client.js (centralizado), auth.js, productos.js, ...
    │   │   ├── context/        # AuthContext.jsx (token memoria)
    │   │   ├── components/     # ProtectedRoute.jsx, Loading, ErrorMessage, ...
    │   │   ├── layout/         # AppLayout.jsx, Header.jsx, NavLinkItem.jsx
    │   │   ├── pages/          # Login.jsx, Productos.jsx, Proveedores.jsx, Movimientos.jsx, Stock.jsx
    │   │   ├── hooks/          # useProductos, useProveedores, ...
    │   │   └── App.jsx + main.jsx + router
    │   └── package.json / vitest.config.js / tailwind.config.js
    ├── app/
    │   ├── models/             # Usuario, Producto, Proveedor, MovimientoInventario, Venta, VentaItem
    │   ├── schemas/            # auth, producto, proveedor, movimiento, stock, venta (Pydantic)
    │   ├── services/           # auth_service, producto_service, movimiento_service, venta_service, deps
    │   ├── routers/            # auth, productos, proveedores, movimientos, stock, ventas
    │   ├── cli/                # crear_usuario.py (bootstrap fuera de API)
    │   └── database.py + main.py
    ├── alembic/ + alembic.ini  # Migraciones (usuarios, productos, proveedores, movimientos, ventas)
    ├── specs/                  # 001..013 con spec/plan/tasks
    │   ├── 001-productos-catalogo/
    │   ├── 002-proveedores/
    │   ├── 003-movimientos-inventario/
    │   ├── 004-consulta-stock/
    │   ├── 005-frontend-base/
    │   ├── 006-frontend-productos/
    │   ├── 007-frontend-proveedores/
    │   ├── 008-frontend-movimientos/
    │   ├── 009-frontend-stock/
    │   ├── 010-frontend-diseno/
    │   ├── 011-autenticacion/
    │   ├── 012-ventas/
    │   └── 013-frontend-autenticacion/
    └── tests/ + nexus.db (SQLite dev)
```

## Estado actual y próximos pasos

**Completado y verificado (469 backend + 322 frontend tests verdes, ruff/mypy verde, `openapi.json` 12 rutas protegidas + 1 pública + docs):**

- Backend 001-004 sin regresión con `Bearer`, 011 `JWT` 8h, 012 `ventas` atómicas con `movimientos_ids` trazables, migraciones `alembic upgrade head` sin pérdida, `Sesion expirada` y `Cerrar sesión` sin `localStorage`.
- Frontend 005 esqueleto + 006-009 CRUD + 010 diseño retroactivo + 013 login con guard `state.from` antes que `404`, `F5` pierde sesión y vuelve a `login` recordando ruta, `Bearer` solo en memoria.

**Fuera de alcance consciente (no se implementa en MVP):**

- Registro público, recuperación/reset de contraseña, roles/permisos, `refresh`/`rotación`, `rate limiting`/CAPTCHA, `nombre`/`rol`/`estado` en usuario, auditoría por usuario, i18n, tema oscuro, notificaciones, responsive móvil, paginación/filtros en `ventas` y `stock`, valorización/lotes/ubicaciones.

**Siguiente spec sugerida si se quiere escalar:**

- `014-frontend-ventas` — UI para `POST /ventas` (selector de productos con stock en vivo, carrito 1-20, `precio_unitario` `Decimal`, `total` derivado, manejo `422`/`404`/`400` con `disponible/solicitado`, y `GET /ventas` historial con `movimientos_ids` clicables hacia `GET /movimientos`).
- O `015-seguridad` — `rate limiting` por IP/email en `POST /auth/login` y `refresh` silencioso, para cerrar la limitación aceptada `011` RNF-5.

---

> **Flujo en una línea:** `Constitución → Spec → Clarificación → Plan → Tasks → Implementación (una tarea cada vez, tests primero) → Validación → Cambio (primero la spec, luego el código).`
> Sesión actual: `Nexus` `013-frontend-autenticacion` T01-T07 completadas, `specs/013` validada como **Cumplida**.

