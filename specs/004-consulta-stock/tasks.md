# Tasks 004 — Consulta de Stock

> Orden por dependencias. Cada tarea 20-30 min. Constitución y `AGENTS.md` vigentes.

- [x] **T01 — Modelo `Producto` añade `stock_minimo`** — RF-1
  - RF: RF-1
  - Hecho cuando: `app/models/producto.py` define `Producto.stock_minimo` `Integer NOT NULL DEFAULT 0 CHECK >=0 AND <=1_000_000`, y `mypy app` pasa.

- [x] **T02 — Schemas Producto extendido y StockResponse** — RF-1
  - RF: RF-1
  - Hecho cuando: `app/schemas/producto.py` acepta `stock_minimo` `Optional[int]` `ge=0 le=1_000_000` (`null`/ausente→0, `""`/`-5`/`>1M`→422) y expone `stock_minimo` en `ProductoResponse`; `app/schemas/stock.py` define `StockResponse` con `codigo/nombre/stock_inicial/stock_minimo/entradas/salidas/stock_actual/alerta` y valida `codigo` `trim+mayúsculas`, y `ruff check .` pasa.

- [x] **T03 — Service `stock_service` cálculo y alerta (reutiliza 003)** — RF-1
  - RF: RF-1
  - Hecho cuando: `app/services/stock_service.py` implementa `calcular_stock(codigo)` y `listar_stock(incluir_inactivos=False)` que reutilizan `movimiento_service._calcular_stock_actual` y calculan `alerta = stock_minimo>0 and stock_actual < stock_minimo`, ordena global por `codigo ASC`, y `mypy app` pasa.

- [x] **T04 — Router `GET /api/v1/stock` y `GET /api/v1/stock/{codigo}` (actualiza para alerta)** — RF-1
  - RF: RF-1
  - Hecho cuando: `app/routers/stock.py` expone `GET ""` con `list[StockResponse]` y `GET "/{codigo}"` con `StockResponse` que delegan a `stock_service`, retornan 200 con `alerta`, 404 si producto no existe/inactivo, 422 si `codigo` formato inválido, sin lógica de negocio en router.

- [x] **T05 — Extender `PATCH /api/v1/productos/{sku}` para `stock_minimo`** — RF-1
  - RF: RF-1
  - Hecho cuando: `app/routers/productos.py` y `app/services/producto_service.py:actualizar_producto` aceptan `stock_minimo` opcional (`null`→0, `""`→422) y actualizan `Producto.stock_minimo` solo si se envía, y `GET /stock` refleja el nuevo `alerta` sin duplicar lógica.

- [x] **T06 — Migración Alembic `agrega stock_minimo a productos`** — RF-1
  - RF: RF-1
  - Hecho cuando: `alembic revision --autogenerate -m "agrega stock_minimo a productos"` genera migración con `add_column stock_minimo` y `CHECK`, y `alembic upgrade head` y `downgrade -1` + `upgrade` pasan sin errores.

- [x] **T07 — Tests unitarios de service stock (mock + sqlite)** — RF-1
  - RF: RF-1
  - Hecho cuando: tests cubren `stock_actual` sin movimientos `==inicial`, `stock_minimo 0`→`false`, `5/5`→`false`, `0` con `mínimo 5`→`true`, `5+10-3=12` con `mínimo 10`→`false` y `7`→`true`, `codigo` normalizado `trim+upper`, `inactivo`→404, `null`/ausente/`""` para `stock_minimo`; `pytest -v` unitarios en verde y `mypy app` pasa.

- [x] **T08 — Tests de integración de endpoints stock (TestClient + DB test)** — RF-1
  - RF: RF-1
  - Hecho cuando: `GET /api/v1/stock` 200 `[]` vacío y `200` con `alerta` para `activos` ordenados, `GET /stock/{codigo}` 200 con `alerta` y 404 para `inexistente`/`inactivo`/`AB`, `POST /productos` con `stock_minimo` y `PATCH` con `stock_minimo` reflejan `alerta` en `GET /stock`, mensajes en español y sin exponer modelos; `pytest -v` integración en verde.

- [x] **T09 — Verificación final constitución + AGENTS.md** — RF-1
  - RF: RF-1
  - Hecho cuando: `pytest -v` 100% verde, `ruff check .` y `ruff format .` sin errores, `mypy app` sin errores, `alembic upgrade head` ok, `GET /docs` lista `GET /stock` y `GET /stock/{codigo}` con `alerta` y `stock_actual` nunca negativo por cálculo.
