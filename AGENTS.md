# AGENTS.md — Sistema de Gestión de Inventario (Tienda de Videojuegos)

## Proyecto
Sistema de gestión de inventario para una tienda de videojuegos: control de stock, productos (juegos, consolas, accesorios), proveedores, ventas y movimientos de inventario. Backend con FastAPI (Python) y PostgreSQL como base de datos, usando SQLAlchemy como ORM y Alembic para migraciones. Arquitectura por capas: `routers/` (endpoints), `services/` (lógica de negocio), `models/` (entidades SQLAlchemy), `schemas/` (Pydantic).

## Comandos
- Ejecutar (dev): `uvicorn app.main:app --reload`
- Instalar dependencias: `pip install -r requirements.txt`
- Migraciones: `alembic upgrade head` / `alembic revision --autogenerate -m "mensaje"`
- Tests: `pytest -v`
- Tests con cobertura: `pytest --cov=app --cov-report=term-missing`
- Lint: `ruff check .`
- Formato: `ruff format .`
- Tipado estático: `mypy app`

## Estilo y convenciones
- Python 3.11+, tipado con type hints en todas las funciones públicas.
- Nombres de variables, funciones y clases en inglés; nombres de dominio del negocio (ej. `videojuego`, `consola`, `stock`) pueden mantenerse en español si así está el resto del código.
- Código y comentarios en español; docstrings breves en funciones de negocio no triviales.
- Modelos SQLAlchemy en singular (`Producto`, `Proveedor`, `MovimientoInventario`); tablas en plural (`productos`, `proveedores`).
- Endpoints REST siguiendo convención `/api/v1/<recurso>`, verbos HTTP estándar (GET, POST, PUT, DELETE).
- Validación de entrada/salida siempre vía schemas Pydantic, nunca exponer modelos SQLAlchemy directamente en la API.
- Commits en español, formato imperativo corto (ej. "agrega endpoint de stock mínimo").

## Reglas
- Lee `docs/constitution.md` y la spec activa antes de tocar código.
- No modificar el esquema de base de datos (tablas, columnas, relaciones) sin generar una migración con Alembic; nunca editar migraciones ya aplicadas en producción.
- No añadir dependencias nuevas al `requirements.txt` sin preguntar antes.
- No tocar la lógica de cálculo de stock (entradas/salidas/reservas) sin revisión explícita, ya que afecta directamente el inventario real.
- No exponer credenciales, tokens ni datos de conexión a la base de datos en el código; todo vía variables de entorno (`.env`, nunca commiteado).
- No eliminar ni modificar registros históricos de movimientos de inventario o ventas; solo se permiten inserciones (append-only) para mantener trazabilidad.

## Al terminar cualquier tarea
- Ejecutar `pytest -v` y confirmar que todos los tests pasan.
- Ejecutar `ruff check .` y `ruff format .` antes de dar por cerrado el cambio.
- Si se modificaron modelos, verificar que exista una migración Alembic generada y aplicable (`alembic upgrade head` sin errores).
- Verificar manualmente que los endpoints afectados respondan correctamente (Swagger en `/docs`). 

Seguir sesion: 
  Session   Constitución proyecto inventario videojuegos
  Continue  opencode -s ses_f841f32caffecaASlKziQ3hMTL

Sesion fronted final 18/09
Session   Implementación T2 habits MVP fase 1 frontend
  Continue  opencode -s ses_f48a3a3e5ffeanKUpbyEXVJL8j