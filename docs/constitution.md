# Constitución — Sistema de Gestión de Inventario

1. **Stack y Arquitectura:** Solo FastAPI + PostgreSQL + SQLAlchemy + Alembic; código estrictamente en `routers/`, `services/`, `models/`, `schemas/`. Verificación: estructura de carpetas y `mypy`/`ruff`.
2. **Spec manda sobre código:** Nada se implementa sin spec activa en `docs/`; todo PR referencia su spec. Verificación: PR enlaza spec, sin spec no hay merge.
3. **Lógica separada de Interfaz:** `routers/` solo HTTP y validación Pydantic; negocio y cálculo de stock solo en `services/`. Verificación: routers sin queries ni lógica de stock.
4. **Tests obligatorios:** Toda lógica nueva con test; `pytest -v` 100% verde antes de merge. Verificación: CI pasa y cobertura sin regresión.
5. **Integridad Append-Only:** Movimientos y ventas nunca se borran/modifican; esquema solo vía migración Alembic versionada. Verificación: `alembic upgrade head` ok y sin DELETE/UPDATE en históricos.
6. **Idioma:** Código, comentarios y commits en español; identificadores en inglés (dominio en español permitido). Verificación: revisión y `ruff format`.
