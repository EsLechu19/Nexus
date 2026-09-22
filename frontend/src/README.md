# Estructura `frontend/src/` — Spec 005 T01

Esqueleto base del panel de inventario. Creado en T01 sin código, solo carpetas vacías para respetar `frontend/docs/constitution.md:3` (stack mínimo) y `frontend/AGENTS.md:20` (centralización API).

## Carpetas

- `api/` — cliente HTTP centralizado (único lugar con `fetch`). RF-3, RF-4, RF-5. Ver `specs/005-frontend-base/plan.md:15-18` y `specs/005-frontend-base/spec.md:36-43`.
- `components/` — componentes presentacionales reutilizables `Loading`, `ErrorMessage`, `EmptyState`, `ConfigErrorBanner`. RF-5, RF-4.
- `layout/` — layout persistente `AppLayout`, `NavLinkItem` con `<nav aria-label>` y `<main>`. RF-1.
- `pages/` — páginas esqueleto `PlaceholderPage` ("En construcción") y `NotFoundPage` (404). RF-2.
- `hooks/` — hooks de estado efímero en memoria (ej. `useApiStatus`). RF-5, RNF-6 (sin localStorage).
- `context/` — estado de sesión volátil `AuthContext` (token solo en memoria, sin localStorage). RF-2, RNF-1, RNF-4 (`013`).

## Reglas

- Ningún componente fuera de `api/` hace `fetch` (`plan.md:43`, constitución §3).
- `VITE_API_URL` solo se lee en `api/client.js` (RF-3).
- Estado solo en memoria, revalidado contra API.

> T01 — Hecho cuando: existen las 5 carpetas vacías + este README. RF-1, RF-2, RF-3, RF-5.
