# Pull Request Template — Nexus
## ¿Qué cambia?
<!-- Enlaza la spec: specs/00X-... y los RF que cubre -->

## Verificación
- [ ] pytest -v verde (backend)
- [ ] ruff check . + ruff format . sin errores
- [ ] mypy app sin errores
- [ ] npm run test verde (frontend)
- [ ] alembic upgrade head sin errores (si tocó modelos)
- [ ] Swagger /docs probado manualmente

