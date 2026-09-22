# Plan 006 — Frontend Productos (Gestión de Catálogo)

## 1. Alineación con constitución y AGENTS — [Cubre todos RF]

- Respeta `frontend/docs/constitution.md:3` stack mínimo (React 18 + Vite + Tailwind + fetch) — sin estado global para RF-1..5.
- Respeta `frontend/docs/constitution.md:5` API aislada — todo HTTP en `src/api/productos.js` vía `src/api/client.js` de 005; ningún `.jsx` hace `fetch` directo — RF-1..5.
- Respeta `frontend/docs/constitution.md:7` estado servidor no cacheado — listado siempre revalidado tras alta/edición/baja, sin `localStorage` — RF-1, RF-5.
- Respeta `frontend/docs/constitution.md:8` idioma español — mensajes genéricos de 005 + mensajes 4xx de `001` ya en español — RF-5, RNF-5.
- Respeta `frontend/AGENTS.md:20` centralización en `src/api/` y `frontend/AGENTS.md:28` validación solo forma — RF-2..4.
- Reutiliza `specs/005-frontend-base/plan.md:3-4,6` cliente `request` tipado (`validacion` vs `conexion`) y componentes `Loading`/`ErrorMessage`/`EmptyState`/`ConfigErrorBanner` — RF-1, RF-5.
- Contratos exactos de `specs/001-productos-catalogo/plan.md:3` (endpoints `/api/v1/productos`, códigos 201/200/400/404/409, normalización SKU, enums) — RF-1..5.

## 2. Estructura de componentes dentro de `frontend/src/` — [Cubre RF-1..5]

```
frontend/src/
├── api/
│   ├── client.js                 # existente 005 — RF-3
│   └── productos.js              # nuevo — RF-1..5 — ver §3
├── pages/
│   └── Productos.jsx             # contenedor de pantalla — RF-1..5 — orquesta listado, modales, revalidación y mensajes éxito
├── components/
│   ├── ProductoTabla.jsx         # presentacional — RF-1 — tabla 4 columnas (sku/nombre/categoria/stock_inicial), sin filtros/paginación
│   ├── ProductoFormModal.jsx     # presentacional + forma — RF-2, RF-3 — modal reutilizado para alta/edición, SKU deshabilitado en edición
│   ├── ProductoBajaDialog.jsx    # presentacional — RF-4 — diálogo confirmación baja lógica
│   ├── ProductoExitoBanner.jsx   # presentacional opcional — RF-2..4 — banner breve 3s "Producto creado/actualizado/dado de baja correctamente" (distinto de ErrorMessage)
│   └── (reutilizados 005) Loading.jsx, ErrorMessage.jsx, EmptyState.jsx — RF-1, RF-5
├── hooks/
│   └── useProductos.js           # estado y lógica de consulta/mutaciones — RF-1..5 — ver §4
└── App.jsx                       # existente — añadir ruta /productos → Productos.jsx — RF-1
```

Responsabilidad:
- `Productos.jsx`: único con `useState` para `productos`, `productoEnEdicion`, `modalAbierto`, `dialogoBajaAbierto`, `errorActivo`, `cargandoPorOperacion`, `mensajeExito`; decide qué componente base mostrar (`Loading` vs `EmptyState` vs `ErrorMessage` vs `ProductoTabla`) según hook; no hace `fetch` directo.
- `ProductoTabla.jsx`: recibe `productos: Array` y callbacks `onEditar(producto)`, `onBaja(producto)`; renderiza `<table>` con 4 columnas, botones Editar/Dar de baja por fila; no conoce API.
- `ProductoFormModal.jsx`: recibe `modo: 'alta'|'edicion'`, `productoInicial`, `onSubmit`, `onClose`, `cargando`, `errorApi`; valida solo forma local y muestra errores de forma inline + error API vía `ErrorMessage` variante `validacion`/`conexion`; SKU deshabilitado en edición.
- `ProductoBajaDialog.jsx`: recibe `producto`, `onConfirmar`, `onCancelar`, `cargando`, `errorApi`; muestra texto confirmación con nombre/SKU y dos botones.
- `useProductos.js`: encapsula `fetch` vía `src/api/productos.js`, expone `{productos, cargandoListado, errorListado, revalidar, crear, editar, baja}` y maneja revalidación sin caché.

> Verificación constitución §3: `grep -r "fetch(" src/components src/pages src/hooks` vacío; solo `src/api/` contiene `fetch`.

## 3. Consumo de endpoints vía cliente centralizado 005 — [Cubre RF-1..5]

`src/api/productos.js` importa `request` de `src/api/client.js` (que valida `VITE_API_URL`, `AbortController` 10s, headers JSON y tipa errores). Cada función construye ruta relativa y deja que `client.js` normalice barra y propague `{tipo:'validacion', reintentable:false}` vs `{tipo:'conexion', reintentable:true}`.

```js
// src/api/productos.js — forma (no código final)
export function listarProductos()  // GET /api/v1/productos → RF-1
export function crearProducto({ nombre, sku, categoria, stock_inicial }) // POST → RF-2
export function editarProducto(sku, { nombre, categoria })               // PATCH /{sku} → RF-3
export function bajaProducto(sku)                                         // DELETE /{sku} → RF-4
```

Ejemplo por operación (contrato `001/plan.md:3`):

**RF-1 GET listado — `listarProductos()`**
- Request: `GET http://api/api/v1/productos` (construido como `request('/api/v1/productos')`)
- Response 200: `[{"sku":"PS5-SLIM-001","nombre":"PlayStation 5 Slim","categoria":"consola","stock_inicial":10}]` → mapeo directo a tabla
- Response 200 vacío: `[]` → `EmptyState`
- Error 4xx/5xx/red → `ErrorMessage` (mensaje API vs genérico)

**RF-2 POST alta — `crearProducto({nombre, sku, categoria, stock_inicial})`**
- Request: `POST /api/v1/productos` body `{"sku":"  ps5-slim-001 ","nombre":"PlayStation 5 Slim","categoria":"consola","stock_inicial":10}` → `client.js` envía `Content-Type: application/json`, SKU normalizado `PS5-SLIM-001` lo hace backend
- Body cuando `stock_inicial` vacío: `{"sku":"X","nombre":"Y","categoria":"videojuego"}` (campo omitido → backend `null→0`, sin traza, respeta `001` RNF-1)
- Response 201: `{"sku":"PS5-SLIM-001","nombre":"...","categoria":"consola","stock_inicial":10,"estado":"activo"}`
- Error 409 duplicado / 400 validación → `ErrorMessage` validacion sin Reintentar; 5xx/red → `conexion` con Reintentar

**RF-3 PATCH edición — `editarProducto(sku, {nombre, categoria})`**
- Request: `PATCH /api/v1/productos/PS5-SLIM-001` body `{"nombre":"... Edición Digital","categoria":"consola"}` (sin `sku`/`stock`/`estado`)
- Response 200: mismo shape con `nombre` actualizado
- Error 400 inmutable/inactivo/validación, 404 no encontrado → validacion

**RF-4 DELETE baja — `bajaProducto(sku)`**
- Request: `DELETE /api/v1/productos/PS5-SLIM-001`
- Response 200: `{"sku":"PS5-SLIM-001","estado":"inactivo",...}`
- Error 400 ya inactivo, 404 no encontrado → validacion

> Todas las llamadas usan `VITE_API_URL` vía `client.js` sin hardcodeo (`AGENTS.md:26`).

## 4. Modelo de estado local — [Cubre RF-1..5, RNF-3]

`Productos.jsx` + `useProductos.js` viven solo en memoria (sin `localStorage`), revalidan tras mutación.

```js
// forma del estado en Productos.jsx (ejemplo ilustrativo)
{
  productos: [],              // Array<{sku,nombre,categoria,stock_inicial}> — RF-1
  cargandoListado: false,     // boolean — RF-1, controla <Loading />
  errorListado: null,         // {tipo, mensaje, reintentable} | null — RF-1
  modal: { abierto: false, modo: 'alta'|'edicion', producto: null }, // RF-2, RF-3
  dialogoBaja: { abierto: false, producto: null }, // RF-4
  operacion: { tipo: null|'alta'|'edicion'|'baja', cargando: false, error: null }, // RF-2..5, deshabilita botón
  mensajeExito: null          // string | null — "Producto creado/actualizado/dado de baja correctamente" — RF-2..4, visible 3s
}
```

`useProductos.js` expone:
- `productos, cargandoListado, errorListado, revalidar()` — RF-1
- `crear(payload)` → `POST` → `revalidar()` — RF-2
- `editar(sku, {nombre,categoria})` → `PATCH` → `revalidar()` — RF-3
- `baja(sku)` → `DELETE` → `revalidar()` — RF-4
- Todos usan `request` tipado y nunca cachean en `localStorage` (constitución §5).

## 5. Contrato de validación de formulario — [Cubre RF-2, RF-3, RNF-1]

**Frontend valida solo forma/UX (sin llamar API), fuente de verdad es API (`AGENTS.md:28`):**

| Campo | Regla forma frontend (sin API) | Mensaje local | Regla negocio backend (API) | Mensaje API |
|-------|-------------------------------|---------------|-----------------------------|-------------|
| `nombre` | requerido tras `trim`, `trim.length >0` | "Nombre requerido" | `2-100` tras trim, permite duplicados | Mensaje 4xx específico (ej. "Nombre debe tener 2-100 caracteres") |
| `SKU` | requerido tras `trim` | "SKU requerido" | `3-20` `^[A-Z0-9_-]+$` tras `trim+mayúsculas`, único global incluye inactivos | `409` "SKU ya existe" o `400` longitud/formato |
| `categoria` | requerido (select no vacío) | "Categoría requerida" | enum exacto `videojuego|consola|accesorio` tras `trim+lower` | `400` "Categoría inválida" |
| `stock_inicial` | si informado, debe ser entero `>=0`, no decimal, no texto; permite vacío | "Stock debe ser entero ≥0" | `int 0..1_000_000`, `null/ausente→0`, `>0` genera traza | `422`/`400` mensaje específico |

- Frontend nunca valida unicidad SKU, rango >1M exacto, ni normalización `trim+mayúsculas` más allá de `trim` para requerido; esos 4xx se muestran tal cual vienen de `001` (en español por `001` RNF-2).
- En edición, `SKU` no se valida (deshabilitado y excluido del payload); `stock_inicial` no se muestra.

## 6. Flujo de cada operación (pseudocódigo) — [Cubre RF-1..5, RNF-2]

**RF-1 Listado — `Productos.jsx` + `useProductos.js`**
```
al montar: estado.cargandoListado=true → render <Loading mensaje="Cargando..." />
  request GET /productos → si ok y array vacío → <EmptyState> "Sin datos disponibles"
                     → si error tipo validacion → <ErrorMessage variante="validacion" mensaje=api>
                     → si error tipo conexion → <ErrorMessage variante="conexion" mensaje="Error de conexión..." onReintentar=revalidar />
  si éxito → set productos → <ProductoTabla> 4 columnas
  botón Reintentar deshabilitado mientras cargandoListado
```

**RF-2 Alta — `ProductoFormModal` modo alta:**
```
usuario click "Crear producto" → modal.abierto=true, modo=alta, producto=null
  usuario completa y submit → valida forma local (requerido) → si falla, muestra inline sin fetch
  si forma ok → operacion={tipo:'alta',cargando:true,error:null} → deshabilita botón "Crear"
    → crearProducto(payload) donde stock_inicial vacío → campo omitido (undefined)
    → si 4xx → operacion.error={tipo:validacion,mensaje:api} → <ErrorMessage variante="validacion"> en modal, mantiene abierto
    → si conexion/5xx → operacion.error={tipo:conexion} → <ErrorMessage variante="conexion" onReintentar=reintentar Alta>
    → si 201 → cierra modal, set mensajeExito="Producto creado correctamente" (banner 3s), revalidar() → GET listado
      → si revalidación falla con conexion → mantiene éxito + muestra ErrorMessage de listado con Reintentar
```

**RF-3 Edición — reutiliza mismo modal:**
```
usuario click "Editar" por fila → modal.abierto=true, modo=edicion, producto=productoFila (precarga nombre/categoria, SKU deshabilitado)
  submit → valida forma (nombre requerido) → si ok → operacion={tipo:'edicion',cargando:true}
    → editarProducto(sku, {nombre,categoria}) // sin sku/stock
    → 4xx (inactivo/no encontrado/inmutable) → mantiene modal + ErrorMessage validacion
    → conexion/5xx → ErrorMessage conexion con Reintentar
    → 200 → cierra modal, mensaje "Producto actualizado correctamente", revalidar()
```

**RF-4 Baja — `ProductoBajaDialog`:**
```
usuario click "Dar de baja" → dialogo.abierto=true con producto → muestra "¿Dar de baja a <nombre> (<SKU>)? No se puede deshacer..."
  cancelar/ESC sin petición → cierra sin efecto
  confirmar → operacion={tipo:'baja',cargando:true} deshabilita Confirmar
    → bajaProducto(sku)
    → 4xx (no encontrado/ya inactivo) → ErrorMessage validacion en diálogo
    → conexion/5xx → ErrorMessage conexion con Reintentar en diálogo
    → 200 → cierra diálogo, mensaje "Producto dado de baja correctamente", revalidar() → si listado pasa de 1→0 muestra EmptyState
  si usuario navega/cierra diálogo mientras cargando → petición no se cancela (AbortController no aborta baja en curso)
```

> Todos los flujos deshabilitan botón disparador mientras `cargando` (`005` RF-5) y usan `ErrorMessage`/`Loading`/`EmptyState` sin variantes.

## 7. Decisiones técnicas justificadas (y alternativa descartada) — [Cubre RF-2..4, RNF-4]

1. **Modal en misma pantalla vs página separada `/productos/nuevo` y `/productos/:sku/editar`**
   - Elegida: modal `ProductoFormModal` y diálogo `ProductoBajaDialog` dentro de `Productos.jsx` (estado local `modal`/`dialogoBaja`).
   - Descartada: rutas separadas para alta/edición.
   - Motivo: `spec.md:98` flujo modal en misma pantalla, sin paginación, más simple para junior (RNF-4), evita duplicar layout y preserva listado visible detrás; página separada obligaría a gestionar navegación y revalidación cruzada innecesaria para 4 campos.

2. **Modal casero con Tailwind (`role="dialog"` + `aria-modal`) vs librería `react-modal`/`headlessui`**
   - Elegida: modal casero con `<div role="dialog" aria-modal="true">` + overlay Tailwind, sin dependencia nueva.
   - Descartada: `react-modal`, `headlessui`, `radix`.
   - Motivo: `AGENTS.md:27` prohibe añadir dependencias sin preguntar y constitución §1 prohíbe UI kit; modal de 4 campos no justifica peso; casero cumple a11y mínima (`label htmlFor`, foco visible, ESC para cerrar) y es comprensible para junior.

3. **Hook `useProductos` vs estado directo en `Productos.jsx`**
   - Elegida: `useProductos.js` encapsula `listar/crear/editar/baja` y revalidación, `Productos.jsx` solo orquesta UI.
   - Descartada: todo el `fetch` y `useState` dentro de `Productos.jsx`.
   - Motivo: separa presentación de lógica (`AGENTS.md:21`), reutilizable para futuros `useProductos` en 008/009, testeable con `fetch` mockeado sin renderizar tabla.

4. **Banner éxito 3s vs toast global**
   - Elegida: `ProductoExitoBanner` inline sobre tabla, visible 3s con `setTimeout`, sin librería toast.
   - Descartada: `react-hot-toast` o notificaciones globales.
   - Motivo: fuera de alcance `005`/`006` (no toasts), banner simple cumple `spec.md:98` sin dependencia y sin estado global.

5. **`stock_inicial` vacío → ausencia/`undefined` vs enviar `0` explícito**
   - Elegida: si input vacío, no incluir `stock_inicial` en payload (o `undefined`) para que backend lo trate como `null→0` sin generar traza, respetando `001` RNF-1 append-only.
   - Descartada: enviar `0` explícito siempre.
   - Motivo: con `0` explícito vs ausente el backend genera traza solo si `>0`; enviar `0` cuando el usuario dejó vacío crearía ambigüedad y no respeta contrato `001` RF-1.

## 8. Estrategia de tests — [Cubre RF-1..5, RNF-1..6, constitución §4]

Stack `Vitest` + `@testing-library/react` + `user-event` + `jsdom`, `fetch` mockeado vía `src/api/client.js` (sin tocar red). Sin escribir código de tests aquí, se define qué se prueba:

**`src/api/productos.js` — unidad (fetch mockeado):**
- RF-1: `listarProductos` resuelve array 4 campos, vacío `[]`, 401/404 → validacion, 500/red → conexion, normaliza ruta sin `//`.
- RF-2: `crearProducto` envía `POST` con `sku` sin `trim` (backend normaliza), `stock_inicial` ausente→undefined, `409` duplicado, `400` longitud/enum, `500` → conexion.
- RF-3: `editarProducto` envía `PATCH` solo `nombre`/`categoria` (sin `sku`), `404`/`400 inmutable` → validacion.
- RF-4: `bajaProducto` envía `DELETE`, `400 ya inactivo` → validacion.
- Verificación `grep -r "fetch(" src/components` vacío.

**`Productos.jsx` — integración con `fetch` mockeado:**
- RF-1: monta → `Loading`, luego `ProductoTabla` 4 columnas o `EmptyState` si `[]`, `ErrorMessage` validacion sin Reintentar vs conexion con Reintentar que re-ejecuta `listar`.
- RF-2: click "Crear producto" abre modal, validación local requerido bloquea `fetch`, submit válido → `POST` + cierra modal + banner "Producto creado correctamente" + `GET` revalidación; `409` mantiene modal con mensaje API; botón deshabilitado mientras `cargando`.
- RF-3: click "Editar" precarga `nombre`/`categoria`, `SKU` deshabilitado y no enviado, `inactivo` sin botón Editar (defensivo), validación local, `PATCH` 200 → cierra + revalida, `404` por carrera muestra mensaje.
- RF-4: click "Dar de baja" abre diálogo confirmación, cancelar cierra, confirmar → `DELETE` + deshabilita Confirmar, `400` mantiene diálogo, `200` → cierra + revalida y si `1→0` muestra `EmptyState`.
- RF-5: `localStorage` nunca usado, `revalidar` siempre llama `GET` tras mutación, `401` tratado como validacion.
- Casos límite: `stock_inicial` `""`→ausencia, `" 0 "`→0, `"1.0"`→400 API, múltiples clics rápidos → una sola petición, revalidación fallida tras éxito mantiene éxito + error listado.

**`ProductoTabla.jsx`, `ProductoFormModal.jsx`, `ProductoBajaDialog.jsx` — unidad presentacional:**
- Tabla renderiza 4 columnas exactas, sin `estado`, sin ordenar; modal con `label htmlFor`/`id`, `role="dialog"`, `SKU` deshabilitado en edición; diálogo con texto `¿Dar de baja a <nombre> (<SKU>)?`.

> Criterio `spec.md:102`: `npm run test` verde, `npm run lint` sin errores, `grep -r "fetch(" src/components|hooks` vacío, español, `lang="es"`.

## 9. Cobertura de RFs — trazabilidad

| Parte del plan | RF cubierto | Evidencia verificable |
|---|---|---|
| `ProductoTabla.jsx` + `Productos.jsx` listado con `Loading`/`EmptyState`/`ErrorMessage` | RF-1 | tabla 4 columnas, sin filtros/paginación, estados 005 |
| `ProductoFormModal.jsx` modo alta + `useProductos.crear` | RF-2 | modal 4 campos, validación solo presencia, 4xx mensaje API, deshabilita cargando, revalida |
| `ProductoFormModal.jsx` modo edición + `useProductos.editar` | RF-3 | SKU solo lectura, payload sin sku/stock, inactivo defensivo, revalida |
| `ProductoBajaDialog.jsx` + `useProductos.baja` | RF-4 | diálogo confirmación, deshabilita Confirmar, 4xx/5xx, revalida y EmptyState 1→0 |
| `useProductos` + `client.js` tipado + deshabilita botones | RF-5 | validacion sin Reintentar vs conexion con Reintentar, `localStorage` vacío, `401` como validacion |
| `a11y` labels, `role=dialog/alert`, `focus-visible:ring`, español | RNF-5, RNF-6 | `label htmlFor`, `lang="es"` |
| Estructura `api/productos.js` sin `fetch` en componentes | Constitución §3, §5 | `grep` vacío fuera de `api` |

## 10. Fuera de alcance del plan (confirmado)

No se diseña búsqueda/filtros, paginación, ordenamiento, detalle inactivos, stock dinámico, `SKU`/`stock` edit, reactivación, borrado físico, importación masiva, i18n, tema oscuro, toasts globales, responsive móvil — tal como `spec.md:88-95`.

## 11. Dudas abiertas

Ninguna bloqueante. No hay `[NECESITA ACLARACIÓN]`; paginación/búsqueda y detalle inactivos se evaluarán en specs futuras si se requieren.
