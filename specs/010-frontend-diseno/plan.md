# Plan 010 — Frontend Sistema de Diseño Visual (Aplicación Retroactiva)

## 1. Alineación con constitución y AGENTS — [Cubre todos RF]

- Respeta `frontend/docs/constitution.md:3` stack mínimo — sin UI kit, solo Tailwind ya elegido en `005`; no añade `Redux`/`Chakra` — RF-1..6.
- Respeta `frontend/docs/constitution.md:5` API aislada — no toca `src/api/`; solo `src/components|pages|layout` y `tailwind.config.js`/`postcss.config.js` — RF-1..6.
- Respeta `frontend/docs/constitution.md:6` Idioma español — mensajes no cambian, solo clases.
- Respeta `frontend/AGENTS.md:20` centralización — no mueve `fetch`; verifica `grep -r fetch` vacío fuera de `src/api` tras refactor visual — RF-6.
- Respeta `frontend/AGENTS.md:27` dependencias — **no añade dependencia nueva**; `tailwind.config.js` y `postcss.config.js` son configuración del stack ya aprobado en `005/plan.md:5`, no librería nueva.
- Reutiliza `specs/005-frontend-base/plan.md:3-4` cliente y `Loading`/`ErrorMessage`/`EmptyState` — RF-6 idéntica.
- En este spec, **LO YA VALIDADO PERMANECE INTACTO** significa comportamiento funcional intacto (endpoint, texto, validación, `disabled`, `ErrorMessage` variante), solo cambia capa visual; tests que asertaban clase literal `bg-red-50` deben actualizarse al nuevo token — RF-1..6.

## 2. Paleta de colores completa — [Cubre RF-1, RF-5]

Valores exactos definidos aquí (única fuente, no en `spec.md`):

**Primario / Acento gamer violeta (profesional sobrio, no neón saturado):**
- `primary-50  #f5f3ff` — fondo suave alerta/hover
- `primary-100 #ede9fe`
- `primary-200 #ddd6fe`
- `primary-300 #c4b5fd`
- `primary-400 #a78bfa`
- `primary-500 #8b5cf6` — **primario/acento principal** (botón primario, `aria-current`, foco)
- `primary-600 #7c3aed` — hover primario
- `primary-700 #6d28d9`
- `primary-800 #5b21b6`
- `primary-900 #4c1d95` — texto sobre fondo claro si necesita contraste

**Neutros (fondo/texto/bordes):**
- `neutral-0   #ffffff` — surface tabla/modal
- `neutral-50  #f9fafb` — fondo app
- `neutral-100 #f3f4f6` — fondo `th`, `EmptyState`
- `neutral-200 #e5e7eb` — borde tabla/input/modal
- `neutral-700 #374151` — texto secundario
- `neutral-900 #111827` — texto primario `td`/`h2`

**Semánticos:**
- `success-50  #ecfdf5` / `success-600 #059669` — `Loading`/`EmptyState` no, solo banner éxito si existiera (hereda `005`)
- `error-50  #fef2f2` / `error-100 #fee2e2` / `error-600 #dc2626` / `error-700 #b91c1c` — `ErrorMessage` validacion vs conexion, botón peligro `Dar de baja`
- `warning-50 #fffbeb` / `warning-600 #d97706` — no usado en MVP, reservado
- `alerta-50  #fef2f2` / `alerta-100 #fee2e2` / `alerta-600 #dc2626` — **reemplaza `bg-red-50` de `009`**: fila en alerta `bg-alerta-50 border-alerta-100`, badge `bg-alerta-100 text-alerta-600`. `alerta` con `false` → sin fondo, `—` en `neutral-700`.

> RF-1, RF-2, RF-5 — **Propia** (paleta violeta no existía en `005` gris base). Verificación: búsqueda `bg-red-50` debe migrar a `bg-alerta-50`.

## 3. Tipografía — [Cubre RF-1]

**Pila completa (con fallback sistema):**
`fontFamily: { sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', 'sans-serif'] }`
Si `Inter` no carga, `system-ui` garantiza legibilidad sin FOIT — `spec.md` fallback.

**Pesos usados (no todos los de Inter):**
- `400` Regular — `td`, `p`, `EmptyState` cuerpo
- `500` Medium — `th`, `label`, botón secundario
- `600` Semibold — `h2`, `badge`, botón primario/peligro
- `700` Bold — `h1` layout (si existe), no usado en tabla para no competir

**Jerarquía y tamaños:**
- `h1` (layout header) `1.875rem`/`30px` `600` `line-height 2.25rem`
- `h2` (Stock/Productos `h2`) `1.25rem`/`20px` `600` `1.75rem`
- `th` `0.75rem`/`12px` `500` `uppercase tracking-wider` `neutral-700`
- `td` `0.875rem`/`14px` `400` `neutral-900`
- `badge` `0.75rem`/`12px` `600` `alerta-600`
- `Loading`/`ErrorMessage`/`EmptyState` `0.875rem` `400/500`
- `input`/`select` `0.875rem` `400`

> RF-1 — **Propia** (Inter no estaba tokenizado en `005/006`).

## 4. Escala de espaciado — [Cubre RF-1, RF-6]

Base `4px`, tokens: `4, 8, 12, 16, 24, 32` (`0.25rem, 0.5rem, 0.75rem, 1rem, 1.5rem, 2rem`).

**Criterio margin vs padding vs gap:**
- `padding` — dentro del componente (`th p-3` = `12px`, `td p-3`, `modal p-6`= `24px`, `badge px-2 py-0.5` = `8/4px`, `input px-3 py-2` = `12/8px`)
- `margin` — entre secciones/componentes (`h2 mb-4` = `16px`, `table mt-4`, `ErrorMessage mt-4`)
- `gap` — entre hijos flex/grid (`nav gap-4` = `16px`, `form gap-4`, `tablist gap-2` = `8px`)
- Nunca `margin` para espacio interno de `th`/`td`; nunca `gap` fuera de flex.

> RF-1 — **Propia** (escala no existía como token en `005`).

## 5. tailwind.config.js y postcss.config.js — [Cubre RF-6, RNF-6]

**Extensión de tokens (ilustrativo, no código final):**
`tailwind.config.js` `theme.extend.colors.primary` con escala `50-900` violeta arriba, `neutral` `50-900`, `success/error/warning/alerta` con `50/100/600`; `fontFamily.sans` con pila Inter+system-ui; `spacing` ya cubre `4,8,12,16,24,32` por defecto, se documenta uso.

`content: ["./index.html","./src/**/*.{js,jsx}"]` — incluye `StockTabla.jsx` para que `bg-alerta-50` no sea purgado aunque solo se use en stock (caso `spec.md:76`).

`postcss.config.js` ya existe con `tailwindcss`+`autoprefixer`; solo se verifica que `tailwind.config.js` sea leído en `dev` y `build` (sin nuevo plugin). No añade dependencia.

> RF-6 — **Propia** (corrección purga) pero idéntica a `005/plan.md:5` en no añadir dependencia.

## 6. Mapeo completo de clases para casos condicionales — [Cubre RF-1, RNF-7]

No concatenación dinámica (`"bg-" + color`). Objeto literal con todas las combinaciones escritas literalmente para que Tailwind las detecte estáticamente.

Ejemplo ilustrativo para alerta (no código final):

```
alertaBadge = {
  true:  "bg-alerta-100 text-alerta-600 border border-alerta-100 px-2 py-0.5 rounded text-xs font-semibold",
  false: "text-neutral-700"
}
filaStock = {
  true:  "bg-alerta-50 border-b border-alerta-100",
  false: ""
}
boton = {
  primario:          "bg-primary-500 text-white hover:bg-primary-600 focus:ring-primary-500",
  primarioDisabled:  "bg-primary-300 text-white cursor-not-allowed",
  secundario:        "bg-white text-neutral-700 border border-neutral-200 hover:bg-neutral-50 focus:ring-primary-500",
  peligro:           "bg-error-600 text-white hover:bg-error-700 focus:ring-error-600",
  peligroDisabled:   "bg-error-300 text-white cursor-not-allowed"
}
inputBase = "bg-neutral-0 border border-neutral-200 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
inputError = "border-error-600 focus:ring-error-600"
```

Cada clave es literal; no hay `bg-${variant}`. Cumple `RNF-7` purga segura.

> RF-1, RF-3, RF-4, RF-5 — **Propia** (mapeo no existía en `006/007/008`).

## 7. Estilos concretos por componente — [Cubre RF-2, RF-3, RF-4, RF-5]

**Tabla `StockTabla`/`ProductoTabla`/`ProveedorTabla`/`MovimientosHistorial` — RF-2:**
- `table` `w-full border-collapse`
- `th` `bg-neutral-100 text-neutral-700 font-medium text-xs uppercase tracking-wider p-3 text-left` (`p-3` = `12px`)
- `td` `p-3 text-sm text-neutral-900 border-t border-neutral-200`
- `tr` separación `divide-y divide-neutral-200`, hover `hover:bg-neutral-50` (excepto fila alerta que mantiene `bg-alerta-50`)
- Sin cambiar `scroll` ni orden.

**Botones — RF-3:**
- Primario: `bg-primary-500 text-white border-transparent hover:bg-primary-600 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2` + `disabled:bg-primary-300`
- Secundario: `bg-white text-neutral-700 border border-neutral-200 hover:bg-neutral-50 focus:ring-primary-500` + `disabled:opacity-50`
- Peligro: `bg-error-600 text-white hover:bg-error-700 focus:ring-error-600` + `disabled:bg-error-300`
- Todos `px-4 py-2 rounded text-sm font-semibold` + `focus:ring-2`.

**Inputs y modales — RF-4:**
- `input/select` `w-full bg-neutral-0 border border-neutral-200 rounded px-3 py-2 text-sm placeholder:text-neutral-700 focus:ring-2 focus:ring-primary-500` ; error `border-error-600 text-error-600`
- `modal overlay` `fixed inset-0 bg-neutral-900/50`
- `modal contenedor` `bg-neutral-0 rounded-lg p-6 gap-4` (`24px`), `h2` `text-xl font-semibold`
- `label` `text-sm font-medium text-neutral-700 mb-1`

**Badges y banners — RF-5:**
- Badge `alerta true` `bg-alerta-100 text-alerta-600 border border-alerta-100` + texto `"Bajo stock"` (no solo color)
- Badge `false` `text-neutral-700` con `"—"`
- `Loading` `text-neutral-700`, `EmptyState` `bg-neutral-0 border border-neutral-200 p-6 text-center`, `ErrorMessage` `bg-error-50 border border-error-100 text-error-700` para `conexion` vs `bg-neutral-0` para `validacion`, `banner éxito` `bg-success-50 border-success-100` (si aplica) — preservan `role="alert"`/`aria-live` ya validado.

> RF-2, RF-3, RF-4, RF-5 — **Propia** en valores, **idéntica** en estructura a `006/008`.

## 8. Qué tests existentes requieren actualizarse — [Cubre RNF-1]

Tests que asertan clase visual literal deben actualizarse al nuevo token (comportamiento no cambia, solo clase):

- `src/components/StockTabla.test.jsx` — aserción `expect(filaAlerta.className).toMatch(/red|bg-red/)` y `bg-red-50` → actualizar a `bg-alerta-50`/`alerta-100` según mapeo §6. Comportamiento `Bajo stock` vs `"—"` no cambia.
- `src/pages/Stock.test.jsx` y `src/hooks/useStock.test.jsx` no — verifican `Bajo stock` texto y `data-alerta`, no clase.
- `src/components/ProductoTabla.test.jsx`, `ProveedorTabla.test.jsx`, `MovimientosHistorial.test.jsx` — si asertan `className` de `th`/`tr`, actualizar a `bg-neutral-100`/`border-neutral-200` si usaban `bg-gray-*`.
- `src/components/MovimientoFormModal.test.jsx`, `ProveedorFormModal.test.jsx` — si asertan `className` de `input` error, actualizar a `border-error-600`.
- Cualquier `structure.test.js` que verifique `tailwind.config` no aplica; solo se actualiza expectativa de clase, no lógica.

Confirmación: ningún test que verifique endpoint llamado, texto mostrado, `disabled`, `EmptyState`, `ErrorMessage` variante o `localStorage` vacío cambia — solo valor esperado de clase.

> RF-1..RNF-1 — **Propia** (listado de actualización).

## 9. Plan de verificación de la corrección Tailwind/PostCSS — [Cubre RF-6, RNF-6]

Pasos concretos, sin código:

1. `npm run dev` — abrir `/productos`, `/proveedores`, `/movimientos`, `/stock` y verificar visualmente que `bg-primary-500` en botón primario, `bg-alerta-50` en fila stock, y `fontFamily Inter` se aplican (inspección `computed style` muestra `Inter` y `rgb(139,92,246)` para primario).
2. `npm run build` + `npm run preview` (o `vite preview`) — repetir verificación en build de producción en mismas 4 rutas; comparar `dev` vs `build` sin diferencias visibles (colores, tipografía, espaciado, `focus:ring`).
3. Inspeccionar `dist/assets/*.css` — buscar `bg-primary-500`, `bg-alerta-50`, `font-` de `Inter`; asegurar que no están purgadas (están literales en mapeo §6 y en `content` de `tailwind.config.js`).
4. `grep -r "bg-" src/components src/pages | sort | uniq` — comprobar que todas las clases usadas están literales en mapeo §6, no concatenadas.
5. `npm run test` verde — confirma que actualización de clases no rompió comportamiento (solo aspecto).
6. `npm run lint` sin errores — confirma que `tailwind.config.js` y `postcss.config.js` son válidos.

> RF-6, RNF-6 — **Propia** (verificación build) pero idéntica a `005/plan.md:5` en no añadir dependencia.

## 10. Decisiones técnicas justificadas — [Cubre RF-1..6]

1. **Tokens en `tailwind.config.js` extend vs CSS variables en `index.css`** — Elegida: `extend` en `tailwind.config.js` (`colors.primary`, `fontFamily`, `spacing` documentado). Descartada: variables `--primary` en `index.css` + `var()`. Motivo: `extend` es estándar Tailwind, detectable estáticamente para purga, y ya existe `tailwind.config.js` en `005`; variables CSS añaden capa y no son necesarias para MVP. *Idéntica a `005` decisión 3 (Tailwind mínimo).*
2. **Objeto de mapeo literal vs concatenación dinámica** — Elegida: objeto con claves literales `bg-alerta-50` etc. Descartada: `` `bg-${color}-50` ``. Motivo: `RNF-7` purga segura; Tailwind solo detecta literales. *Propia (no existía en `006/008`).*
3. **Badge+fila vs solo badge o solo fila** — Elegida: ambos (badge texto + fila `bg-alerta-50`), nunca solo color. Descartada: solo fila `bg-red-50` sin badge. Motivo: `RNF-4` accesibilidad, badge es fuente de verdad para lector. *Propia, ya validada en `009`.*
4. **Unificar `Loading`/`ErrorMessage`/`EmptyState` vs dejarlos con estilos viejos** — Elegida: unificar con nuevos tokens `neutral`/`error`/`success`. Descartada: dejarlos con `bg-gray` viejo. Motivo: `RNF-2` consistencia en 4 pantallas; si se dejan viejos, `010` no sería retroactivo completo. *Propia.*

## 11. Estrategia de tests — [Cubre RF-1..6, constitución §4]

Stack `Vitest` + `Testing Library` + `jsdom`, `fetch` mockeado vía `client.js`. Sin escribir código de tests aquí.

- **Actualización de tests existentes** (ver §8): `StockTabla` y `ProductoTabla` que asertaban `bg-red-50`/`bg-gray` se actualizan a `bg-alerta-50`/`bg-neutral-100` — solo cambia `expect(...).toMatch(/bg-alerta-50/)`, no lógica.
- **`StockTabla` — unidad:** verifica `5 cols` con `th` `bg-neutral-100`, `td` `p-3`, fila `alerta true` tiene `bg-alerta-50` + badge `bg-alerta-100`, `false` tiene `"—"` sin clase alerta, `stock_minimo 0` como `"0"`.
- **`Stock` — integración:** monta→`Loading` con `text-neutral-700`, luego `StockTabla` con `border-neutral-200` o `EmptyState` con `bg-neutral-0`, error `validacion` sin `bg-error` vs `conexion` con `border-error-100`.
- **`Botones` — unidad (nuevo):** primario `bg-primary-500` vs `bg-primary-300` disabled, secundario `bg-white border-neutral-200`, peligro `bg-error-600`; `focus:ring-primary-500` presente.
- **`Inputs/Modales` — unidad:** `input` `border-neutral-200` normal vs `border-error-600` con error, `focus:ring-primary-500`.
- **Verificación `grep`:** `grep -r "bg-" src/components | grep -v "bg-alerta-50\|bg-primary-500\|..."` debe ser vacío salvo mapeo literal; `grep -r "fetch("` vacío fuera de `src/api`.

> RF-1..6 — **Análoga a `008 §10` pero sin `fetch` de stock (propia para estilo).

## 12. Cobertura de RFs — trazabilidad

| Parte del plan | RF cubierto | Evidencia verificable | Reutilizado de `005`/`006`/`008`/`009` |
|---|---|---|---|
| Paleta `primary`/`neutral`/`alerta` + `Inter` + `spacing 4` en `tailwind.config.js` | RF-1 | `bg-primary-500` en primario, `Inter` en `computed`, `p-3`=`12px` en `th`/`td` | Propia (tokens) |
| `StockTabla` 5 cols badge+fila `alerta` | RF-1, RF-2 | `—` vs `Bajo stock` + `bg-alerta-50` | Propia (009) + Tokens |
| `Stock` + `useStock` con `Loading`/`EmptyState`/`ErrorMessage` | RF-1, RF-2 | `Loading` `Cargando...`, `EmptyState` para `[]`/`null` | Sí (009) |
| Botones `primario/secundario/peligro` + `disabled`/`focus` | RF-3 | `bg-primary-500` vs `bg-error-600`, `disabled:bg-*`, `focus:ring` | Propia (jerarquía) |
| Inputs `border-neutral-200` + `focus:ring` + modales `p-6` | RF-4 | `border-error-600` en error, `label` asociado | Sí (006) + Tokens |
| Badges `bg-alerta-100` + banners `bg-success/error-50` | RF-5 | badge+fila nunca solo color | Propia |
| `tailwind.config.js` `content` + mapeo literal + `postcss` | RF-6 | `dev` vs `build` idénticos, `dist/*.css` contiene `bg-alerta-50` | Sí (005) + RNF-7 |
| Tests actualizados `bg-red-50`→`bg-alerta-50` | RNF-1 | `npm run test` verde, comportamiento `Bajo stock` no cambia | Propia |

## 13. Fuera de alcance del plan (confirmado)

No se diseña modo oscuro, cambio de paleta por usuario, responsive móvil, animaciones complejas, iconografía nueva más allá de `Inter`/colores/espaciado, branding definitivo, nueva funcionalidad validada, filtros/paginación/ordenamiento — tal como `spec.md:79-85`.

## 14. Dudas abiertas

- Ninguna bloqueante. Definición hex exacta ya dada en §2 (violeta `500 #8b5cf6` etc.), por lo que `spec.md:94` "sin [NECESITA ACLARACIÓN]" se mantiene; `Inter` con fallback `system-ui` y escala `4,8,12,16,24,32` ya definidas, no bloquean.
