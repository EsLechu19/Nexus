# Constitución — Nexus Frontend

1. **Stack mínimo:** Solo React 18 + Vite + Tailwind + fetch nativo; prohibido estado global (Redux/Zustand) o UI kits sin aprobación. Verificación: `package.json` sin deps extra y `grep -r fetch src/components` vacío.
2. **Spec → Componentes:** Aplica raíz §2. Ningún componente/ruta sin `specs/00X-frontend-*/spec.md` que lo exija. Verificación: PR enlaza spec.
3. **API aislada de UI:** Todo HTTP en `src/api/`; `.jsx` nunca hace `fetch` directo. Verificación: `grep -r "fetch(" src/components src/hooks` vacío.
4. **Tests de componente:** Aplica raíz §4. Cada componente con lógica prueba loading/error/success con `fetch` mockeado. Verificación: `npm run test` verde.
5. **Estado servidor no cacheado:** Solo estado local efímero (inputs, modales); stock/productos siempre vía API y revalidado tras mutación. Verificación: sin `localStorage` para inventario, refetch tras POST/PUT.
6. **Idioma:** Aplica raíz §6. Código/comentarios y mensajes UI en español. Verificación: revisión manual.
