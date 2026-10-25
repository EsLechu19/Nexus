# Backend/frontend replacement

## Objetivo

Continuar el reemplazo de forma incremental, preservando contratos y trazabilidad, empezando por cerrar la atomicidad de ventas en PostgreSQL.

## Alcance autorizado

- Tarea actual: T1.4 — atomicidad de ventas y operación canónica de movimientos.
- No modificar esquema ni crear migraciones.
- No cambiar contratos de `/api/v1/ventas` ni `/api/v1/movimientos`.
- No modificar frontend en esta tarea.
- PostgreSQL real para evidencia de concurrencia; SQLite no cuenta como evidencia de runtime.

## Tareas

- [x] T1.4 — Caracterizar y corregir atomicidad de ventas, items y movimientos.
- [x] T1.7 — Resolver el gate de rollback después de cerrar T1.4.

## Criterios de aceptación T1.4

- Venta multiítem exitosa crea una venta, sus items y sus movimientos dentro de una unidad transaccional.
- Cualquier fallo revierte venta, items, movimientos y cambios de stock.
- Producto inexistente, inactivo o stock insuficiente no deja efectos parciales.
- La operación de salida usa un camino canónico sin duplicar commits.
- La evidencia de concurrencia usa PostgreSQL real y no permite stock negativo.

## Ruta y verificación

- Ruta: worker único delegado; toca múltiples archivos no triviales.
- TDD estricto: deshabilitado por configuración existente.
- Checks: tests focalizados, PostgreSQL real para concurrencia, suite backend, Ruff, formato y mypy.
- Estado: T1.4 y T1.7 completadas.

## Evidencia T1.4

- **Estado:** completada con evidencia PostgreSQL real.
- **Archivos:** `app/services/venta_service.py`,
  `app/services/movimiento_service.py` y
  `tests/test_t14_venta_atomicidad_postgresql.py`.
- **Corrección:** las validaciones, locks, venta, `venta_items`, movimientos y
  stock comparten un único `UnitOfWork`; la salida canónica
  `preparar_salida` no hace commit; se adquieren locks de productos en orden
  estable para evitar deadlocks entre ventas multiítem.
- **Casos cubiertos:** venta multiítem exitosa; rollback por producto
  inexistente, inactivo, stock insuficiente y fallo inyectado; un solo commit;
  concurrencia PostgreSQL real con no-negatividad de stock, marcada `skip` con
  razón explícita cuando no existe URL PostgreSQL.
- **Checks:** `python -m pytest -v` → 515 passed, 3 skipped; prueba focalizada
  de ventas/movimientos → 27 passed, 1 skipped; `python -m ruff check` sobre
  archivos afectados → OK; `python -m ruff format --check` sobre archivos
  afectados → OK; `python -m mypy app --ignore-missing-imports` → OK.
- **Evidencia final:** `python -m pytest -v tests/test_t14_venta_atomicidad_postgresql.py`
  → **5 passed** contra PostgreSQL real, incluyendo concurrencia sin stock
  negativo. Commit: `d5745ef asegura atomicidad de ventas`.
- **Bloqueo restante:** ninguno para T1.4; el gate de rollback se documenta en
  la evidencia T1.7.

## Evidencia T1.7

- **Estado:** completada con validación de CI y merge en `master`.
- **Corrección validada:** `frontend/src/components/ProductoFormModal.jsx`
  inicializa los campos de edición desde `producto`, evitando que el primer
  render exponga un SKU vacío.
- **Checks focalizados:** `npm test -- --run src/pages/Productos.test.jsx`
  → 18 passed; suite frontend → 322 passed.
- **CI:** PR #1 pasó Backend — ruff / mypy / pytest y Frontend — vitest / build.
- **Punto de rollback conocido:** commit `28f8318` (`master`), merge squash
  del PR #1. Este commit es el último estado validado de la corrección.
