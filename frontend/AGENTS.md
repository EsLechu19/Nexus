# AGENTS.md — Nexus Frontend (Panel de Inventario)

## Proyecto
Frontend del sistema de gestión de inventario para la tienda de videojuegos: interfaz web para gestionar productos, proveedores, movimientos de inventario y consulta de stock. Consume la API REST del backend (FastAPI) documentada en `../specs/*/plan.md` y expuesta vía OpenAPI en `/docs`. React 18 + Vite como bundler, JavaScript (sin TypeScript por ahora), Tailwind CSS para estilos, `fetch` nativo para llamadas HTTP (sin librería de manejo de estado global).

## Comandos
- Instalar dependencias: `npm install`
- Ejecutar (dev): `npm run dev`
- Build de producción: `npm run build`
- Tests: `npm run test`
- Lint: `npm run lint`
- Formato: `npm run format`

## Estilo y convenciones
- JavaScript ES2022+, módulos ES (`import`/`export`), sin TypeScript en el MVP.
- Un componente por archivo, nombre de archivo y componente en `PascalCase` (ej. `ProductoForm.jsx`).
- Hooks personalizados con prefijo `use` (ej. `useProductos.js`), en `camelCase`.
- Variables, funciones y props en `camelCase`; nombres de dominio del negocio (ej. `producto`, `proveedor`, `stockMinimo`) pueden mantenerse en español si así está el resto del código.
- Código y comentarios en español; docstrings/JSDoc breves en funciones no triviales.
- Toda llamada a la API centralizada en `src/api/` (un archivo por recurso: `productos.js`, `proveedores.js`, `movimientos.js`); ningún componente hace `fetch` directo.
- Componentes de presentación separados de componentes con lógica/estado cuando la complejidad lo justifique.
- Commits en español, formato imperativo corto (ej. "agrega formulario de alta de proveedor").

## Reglas
- Lee `docs/constitution.md` y la spec activa (`specs/00X-frontend-*/spec.md`) antes de tocar código.
- No hardcodear la URL base de la API: siempre vía variable de entorno (`.env`, nunca commiteado; usar `.env.example` como referencia).
- No añadir dependencias nuevas (librerías de estado, UI kits, routing, etc.) al `package.json` sin preguntar antes.
- No duplicar validaciones de negocio ya resueltas en el backend (ej. reglas de stock, unicidad de SKU); el frontend valida solo forma/UX (campos requeridos, formato), la fuente de verdad es la API.
- No modificar contratos de la API desde el frontend: si un endpoint no devuelve lo que se necesita, se ajusta el `plan.md` del spec de backend correspondiente, no se improvisa en el cliente.
- No commitear credenciales ni tokens; toda configuración sensible vía variables de entorno.

## Al terminar cualquier tarea
- Ejecutar `npm run lint` y confirmar que no hay errores.
- Ejecutar `npm run test` y confirmar que todos los tests pasan.
- Verificar manualmente en el navegador (`npm run dev`) que la pantalla afectada funciona contra el backend real corriendo en local.
- Si se agregó o modificó una llamada a la API, confirmar que coincide exactamente con el contrato definido en el `plan.md` del spec de backend correspondiente.
