# Estabilizar PostgreSQL

## Objetivo

Corregir los problemas actuales de configuración, migraciones, CI, pruebas y documentación sin rehacer Nexus ni migrar datos de `nexus.db`.

## Alcance autorizado

- PostgreSQL 18 como único runtime operativo.
- Base local vacía `nexus_dev`.
- Migraciones Alembic nuevas únicamente; no editar migraciones aplicadas.
- No tocar credenciales ni versionar `.env`.
- Mantener la arquitectura y los contratos existentes.

## Tareas

- [x] EST-001 — Cargar `.env` de forma segura y validar precedencia de variables.
- [x] EST-002 — Corregir el ancho de `movimientos_inventario.tipo` mediante migración forward-only y prueba PostgreSQL.
- [ ] EST-003 — Validar la cadena completa de Alembic online y offline contra PostgreSQL.
- [x] EST-004 — Migrar CI y pruebas de integración a PostgreSQL 18.
- [x] EST-005 — Actualizar README y documentación operativa para eliminar SQLite como runtime.
- [ ] EST-006 — Ejecutar la verificación completa y registrar los fallos restantes sin ocultarlos.
- [x] EST-007 — Crear baseline PostgreSQL limpio para bases vacías y conservar la cadena histórica sin modificarla.
- [x] EST-008 — Adaptar la suite restante al baseline PostgreSQL y eliminar fixtures SQLite incompatibles.

## Criterios de aceptación

- `alembic upgrade head` funciona contra `nexus_dev`.
- La columna `movimientos_inventario.tipo` acepta `entrada_inicial` sin truncamiento.
- Una base PostgreSQL vacía puede ejecutar `alembic upgrade head` desde el baseline limpio.
- La CI provisiona PostgreSQL y no define `sqlite:///`.
- Las pruebas que validan persistencia, migraciones o concurrencia usan PostgreSQL.
- `pytest -v`, `ruff check .`, `ruff format --check .` y `mypy app --ignore-missing-imports` tienen resultados registrados.

## Progreso

- Ruta: implementación directa delegada por tarea.
- Estado: EST-001 completada; verificación focalizada aprobada.
- Evidencia EST-001: `python -m pytest -v tests/test_postgresql_config.py` (11 passed), `python -m pytest -v tests/test_alembic_postgresql_only.py` (3 passed) y `ruff check app/config.py tests/test_postgresql_config.py` sin errores. El ejecutable directo `pytest -v` no pudo importar `app` en este entorno (`ModuleNotFoundError`), mientras que la invocación equivalente por módulo sí completó las pruebas.
- Estado: EST-002 completada; la migración `a1b2c3d4e5f6` amplía `tipo` a `VARCHAR(15)` y su downgrade rechaza truncamientos. La prueba PostgreSQL se omite honestamente si `DATABASE_URL` no está disponible.
- Evidencia EST-002: `python -m pytest -v tests/test_migracion_tipo_movimiento_EST002.py` (1 passed, 1 skipped), `python -m ruff check alembic/versions/a1b2c3d4e5f6_amplia_tipo_movimientos_inventario.py tests/test_migracion_tipo_movimiento_EST002.py` sin errores y `python -m alembic history` confirma el nuevo head. `alembic upgrade head --sql` queda bloqueado por la migración histórica `9111dba96a53`, que usa `batch_alter_table` con reflexión y requiere conexión PostgreSQL.
- Estado: EST-003 no aprobada: la validación encontró incompatibilidades históricas que no se pueden corregir con una migración posterior sin alterar la cadena ejecutada. `alembic history` confirma el head `a1b2c3d4e5f6`. Con `DATABASE_URL=postgresql://test:test@localhost:5432/nexus_dev`, `python -m alembic upgrade head --sql` falla explícitamente antes de emitir SQL por `9111dba96a53` y `7010b4ddca09`, que usan `batch_alter_table(..., recreate='always')` y requieren reflexión PostgreSQL en vivo. La ejecución online contra PostgreSQL también falla en `7010b4ddca09`: el recreado de `productos` intenta eliminar `productos_pkey` mientras `movimientos_inventario_producto_id_fkey` depende de ella. `alembic/env.py` añade el fallo offline explícito y no modifica migraciones aplicadas; EST-003 requiere una decisión específica sobre la cadena histórica antes de poder marcarse completa.
- Evidencia EST-004: `.github/workflows/ci.yml` provisiona `postgres:18`, usa la base aislada `nexus_test`, inyecta una `DATABASE_URL` PostgreSQL no sensible y ejecuta `alembic upgrade head` antes de pytest. `tests/test_ci_postgresql.py` verifica estáticamente que CI no contenga `sqlite:///` y mantiene el orden de migración antes de pruebas. Validación focalizada: `python -m pytest -v tests/test_ci_postgresql.py tests/test_postgresql_config.py` (13 passed). No se ejecutó la pipeline remota.
- Estado: EST-005 completada; `README.md`, `.env.example` y `docs/migration-runbook.md` establecen PostgreSQL 18 como obligatorio para aplicación, Alembic, pruebas de integración y CI, nombran `nexus_dev` como base de desarrollo vacía y dejan `nexus.db` como archivo archivado/no operativo sin copia automática de datos. La búsqueda focalizada de instrucciones operativas no encontró URLs SQLite en esos documentos ni en CI. No se modificaron código, migraciones, CI ni `.env`.
- Estado: EST-006 verificación ejecutada el 2026-10-24; no aprobada por fallos reales registrados abajo. Las tareas EST-001, EST-002, EST-004 y EST-005 permanecen marcadas completas y cada una conserva una línea de evidencia explícita; no se modificaron sus casillas.
- Evidencia EST-006 — `python -m pytest -v`: **FAIL** — 487 passed, 1 skipped, 12 failed y 10 warnings en 500 tests. Los fallos de `alembic upgrade head` reproducen el bloqueo histórico de `7010b4ddca09`: PostgreSQL rechaza eliminar `productos_pkey` porque `movimientos_inventario_producto_id_fkey` depende de ella. También falla `test_validar_existencia_y_activo_404_400` por `sqlite3.OperationalError: no such table: productos`, y falla la prueba de configuración que esperaba rechazar una URL inválida sin exponerla. La invocación fue por módulo para importar correctamente el paquete.
- Evidencia EST-006 — `ruff check .`: **PASS** — `All checks passed!`.
- Evidencia EST-006 — `ruff format --check .`: **PASS** — 134 files already formatted.
- Evidencia EST-006 — `mypy app --ignore-missing-imports`: **PASS** — `Success: no issues found in 39 source files`.
- Evidencia EST-006 — `alembic history`: **PASS** — el head reportado es `a1b2c3d4e5f6`.
- Evidencia EST-006 — `alembic upgrade head`: **BLOCKED** — `DATABASE_URL` está ausente o vacío en el proceso, por lo que esta verificación no se ejecutó directamente conforme a la restricción de no usar `.env` ni imprimir secretos. La suite de pytest sí ejecutó pruebas internas que invocan Alembic mediante la configuración cargada por la aplicación y reprodujo el fallo de dependencia PostgreSQL descrito arriba.
- Estado: EST-007 completada; se creó `alembic-baseline.ini` con raíz independiente `alembic_baseline/` y migración `000000000001` (`down_revision=None`) para el esquema actual. La cadena histórica en `alembic/` no fue modificada. El baseline rechaza SQLite y `upgrade` sobre cualquier tabla pública existente antes de abrir la transacción de migración. `current` es solo lectura y `stamp` se permite únicamente cuando existen las seis tablas del esquema baseline, para reparar una base cuyo esquema ya fue creado pero cuya tabla `alembic_version` está vacía.
- Evidencia EST-007 — `python -m pytest -v tests/test_baseline_postgresql_EST007.py tests/test_alembic_baseline_config_EST007.py`: **PASS** — 7 passed. La forma literal solicitada `pytest -v ...` queda **BLOCKED/FAIL de entorno** por el `ModuleNotFoundError: No module named 'app'` ya observado en este checkout; la invocación equivalente por módulo sí completó la prueba.
- Evidencia EST-007 — `python -m ruff check .`: **PASS** — `All checks passed!`.
- Evidencia EST-007 — `python -m ruff format --check .`: **PASS** — 138 files already formatted.
- Evidencia EST-007 — `python -m alembic -c alembic-baseline.ini history`: **PASS** — `000000000001` es el head baseline.
- Evidencia EST-007 — `python -m alembic -c alembic.ini history`: **PASS** — la cadena histórica conserva `a1b2c3d4e5f6` como head.
- Evidencia EST-007 — `DATABASE_URL=<URL PostgreSQL local de prueba> python -m alembic -c alembic-baseline.ini upgrade head`: **BLOCKED** — no hay PostgreSQL local disponible; no se ejecutó contra `nexus_dev`, no se usó `.env` y no se expusieron credenciales. Instrucción exacta para el usuario: inyectar una URL PostgreSQL 18 válida a `nexus_dev` y repetir `alembic -c alembic-baseline.ini upgrade head`.
- Evidencia EST-007 — prueba reproducible: el modo offline emite el `INSERT INTO alembic_version` de `000000000001`; además, si el esquema baseline existe y `alembic_version` está vacío, `current` ya no queda bloqueado y `stamp head` puede registrar `000000000001`; `upgrade` continúa rechazando la base no vacía. Pruebas focalizadas: `python -m pytest -v tests/test_baseline_postgresql_EST007.py tests/test_alembic_baseline_config_EST007.py` (11 passed).
- Evidencia adicional — la ejecución local de `python -m alembic -c alembic-baseline.ini current -v` encontró una base `nexus_dev` sin tablas, por lo que el estado exacto "esquema creado + versión vacía" no pudo reproducirse sin modificar la base del usuario. El SQL offline confirma que un `upgrade` exitoso sí debe insertar `000000000001`; un caso real de versión vacía requiere revisar que `upgrade` y `current` hayan usado la misma `DATABASE_URL`, o aplicar la reparación `stamp` documentada.
- Evidencia adicional — `python -m pytest -v`: **FAIL** — 497 passed, 1 skipped y 13 failed; los fallos restantes pertenecen a la cadena histórica PostgreSQL (`7010b4ddca09` intenta eliminar `productos_pkey` con una FK dependiente), pruebas antiguas SQLite/configuración y no al baseline corregido.

### Actualización del baseline online — 2026-10-24

- Estado: EST-003 queda **parcialmente resuelta para el baseline independiente**. La causa exacta del incidente original no puede atribuirse solo a `env.py`: la documentación de Alembic confirma que `context.begin_transaction()` sobre una conexión online debe abrir una transacción real y confirmarla, y este entorno no tiene PostgreSQL para reproducir el caso contra `nexus_dev`. Sí se corrigió una debilidad verificable: el baseline no tenía una frontera transaccional explícita de SQLAlchemy ni una verificación posterior, por lo que no podía convertir un falso éxito en error.
- Corrección mínima: `run_migrations_online()` usa `connectable.begin()` como frontera transaccional externa, configura `transactional_ddl=True` y verifica antes del commit las seis tablas y `public.alembic_version = 000000000001`. No se añadió `connection.commit()`, no se usa `CASCADE`, no se borran datos y no se modificaron migraciones históricas.
- Modelo transaccional: PostgreSQL soporta DDL transaccional; `engine.begin()` confirma la unidad completa al salir sin excepción y revierte DDL y `alembic_version` si la verificación o la migración falla. La verificación posterior convierte un falso éxito en un error antes de confirmar. La hipótesis alternativa —URL efectiva distinta de `nexus_dev` o una ejecución previa diferente— debe comprobarse en el servidor con la URL no expuesta.
- Prueba focalizada: `tests/test_baseline_postgresql_EST007.py` exige la frontera transaccional y contiene una prueba online reproducible que solo corre con `NEXUS_BASELINE_TEST_DATABASE_URL` apuntando a una base PostgreSQL de prueba vacía. Sin esa variable se omite con razón; no pasa falsamente ni toca `.env`.
- Estado real de ejecución: PostgreSQL no está disponible en este entorno (`DATABASE_URL` no está definido), por lo que la prueba online quedó omitida y no se ejecutó `nexus_dev`. La prueba offline sigue siendo evidencia de SQL generado, no de persistencia.
- La cadena histórica de `alembic/` continúa bloqueada por los problemas documentados de `7010b4ddca09`; esta corrección solo afecta `alembic-baseline.ini` y conserva el rechazo de bases no vacías y el comportamiento `current`/`stamp`.

### Evidencia EST-008 — 2026-10-24

- Se adaptaron los comandos de la suite antigua que consultan el estado operativo a `-c alembic-baseline.ini` y expectativa `000000000001`; las pruebas que inspeccionan mensajes de la cadena histórica mantienen `alembic.ini` explícito.
- Se hizo tolerante la aserción estática de CI a la forma real `alembic -c alembic-baseline.ini upgrade head` y `PYTHONPATH=. pytest -v`, conservando PostgreSQL obligatorio, ausencia de SQLite y orden migración antes de pytest.
- La prueba de secretos aísla `DOTENV_PATH` a un archivo inexistente; mantiene la exigencia de `JWT_SECRET_KEY` en producción y verifica que la URL no se divulgue. No se modificó `.env`.
- `test_validar_existencia_y_activo_404_400` dejó de crear SQLite en memoria y usa una sesión simulada explícita para cubrir 404, 400 y éxito sin contradecir PostgreSQL como único runtime.
- Evidencia focalizada: `python -m pytest -v tests/test_baseline_postgresql_EST007.py tests/test_ci_postgresql.py tests/test_phase1_safety_seams.py tests/test_venta_validacion_T03_012.py`: **22 passed, 1 skipped**. El skip es la prueba online de PostgreSQL por ausencia de `NEXUS_BASELINE_TEST_DATABASE_URL`; no se inventó PASS ni se imprimió ninguna URL.
- Evidencia completa: `python -m pytest -v`: **511 passed, 2 skipped, 10 warnings**.
- Evidencia de calidad: `python -m ruff check .` **PASS**; `python -m ruff format --check .` **PASS** (138 archivos); `python -m mypy app --ignore-missing-imports` **PASS** (39 archivos).

### Reparación no destructiva de `nexus_dev`

Si `nexus_dev` ya contiene el esquema baseline y `alembic_version` no tiene filas, no se debe ejecutar `upgrade` ni borrar tablas. Verificar primero, sin mostrar la URL ni credenciales, que existan `productos`, `proveedores`, `movimientos_inventario`, `usuarios`, `ventas` y `venta_items`. Luego ejecutar:

```bash
alembic -c alembic-baseline.ini stamp head
alembic -c alembic-baseline.ini current -v
```

El primer comando solo registra `000000000001` en `alembic_version`; no ejecuta la migración ni usa `CASCADE`. Si falta alguna tabla, o existen dudas sobre el origen del esquema, detenerse y hacer una copia/diagnóstico antes de usar `stamp`. Una base vacía nueva debe seguir usando exclusivamente `alembic -c alembic-baseline.ini upgrade head`.
