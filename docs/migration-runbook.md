# Runbook operativo de PostgreSQL 18

Este runbook prepara una base de desarrollo vacía y valida el esquema sin
exponer credenciales ni tocar datos de producción.

## Alcance y límites

- PostgreSQL 18 es obligatorio para la aplicación, Alembic, las pruebas de
  integración y CI.
- La base local de desarrollo se llama `nexus_dev`.
- `nexus.db` queda archivado y no operativo. No es fallback, fuente de datos ni
  entrada automática para este procedimiento.
- No se copian ni importan datos automáticamente. La base comienza vacía.
- No se debe ejecutar este procedimiento contra producción.

## Preparar el entorno

1. Crea o dispone una instancia local de PostgreSQL 18 y una base vacía llamada
   `nexus_dev`.
2. Copia `.env.example` a `.env` y reemplaza sus marcadores localmente. También
   puedes inyectar las variables en la sesión:

   ```powershell
   $env:DATABASE_URL="postgresql://<user>:<password>@localhost:5432/nexus_dev"
   $env:JWT_SECRET_KEY="<secret-local-de-al-menos-32-caracteres>"
   ```

3. No guardes la URL completa ni el secreto en documentación, logs o commits.

## Aplicar y validar el esquema

Desde la raíz del repositorio:

```powershell
alembic -c alembic-baseline.ini upgrade head
```

La ejecución debe completarse contra PostgreSQL 18 y `nexus_dev`. Este comando
selecciona explícitamente el baseline limpio (`alembic_baseline/`) y solo acepta
una base sin tablas ni una versión Alembic previa. Si encuentra cualquier tabla,
incluida `alembic_version`, se detiene sin modificarla. No uses este comando
contra una base existente.

La configuración histórica permanece disponible con `alembic.ini` y
`alembic/` únicamente para inspección. No uses `alembic upgrade head` sin
`-c alembic-baseline.ini` para preparar una base nueva: esa orden selecciona la
cadena histórica rota.

Después ejecuta las pruebas de integración y los chequeos definidos por CI:

```powershell
pytest -v
ruff check .
ruff format --check .
mypy app --ignore-missing-imports
```

Para una comprobación offline acotada a una revisión compatible, genera SQL sin
aplicar cambios:

```powershell
alembic -c alembic-baseline.ini upgrade head --sql
```

El modo offline no puede comprobar si la base destino está vacía; el rechazo de
SQLite y de bases no vacías solo se verifica en el flujo online. Para inspeccionar
la cadena histórica, usa `alembic -c alembic.ini history`; no la ejecutes contra
`nexus_dev`.

Las pruebas de persistencia, migraciones y concurrencia deben evidenciar el
camino PostgreSQL. Una prueba aislada no convierte `nexus.db` en runtime.

## Credenciales y diagnóstico

Las credenciales se entregan por variables de entorno o por el mecanismo de
secretos de CI. Los diagnósticos deben redactar usuario, contraseña, tokens y
la URL completa. Si una comprobación falla, corrige la inyección local sin
copiar secretos al repositorio.

## Archivo y rollback

Conserva `nexus.db` como archivo histórico de solo lectura si existe. No lo
modifiques, borres ni uses para rellenar `nexus_dev`. Un fallo de validación se
resuelve deteniendo la operación y conservando la evidencia; no se eliminan
filas, no se degrada Alembic y no se restaura automáticamente el archivo.
