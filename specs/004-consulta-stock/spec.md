# Spec 004 — Consulta de Stock

## Contexto y objetivo
La tienda necesita conocer el stock actual de cada producto para evitar quiebres y generar alertas cuando un producto cae por debajo de su stock mínimo. Esta funcionalidad es de solo lectura: interpreta los productos (001) y los movimientos (003) para calcular `stock_actual = stock_inicial + entradas - salidas` y exponerlo con alerta. No crea ni modifica productos ni movimientos; solo los consulta y deriva el estado. Introduce `stock_minimo` como extensión del catálogo de productos (columna nueva en `productos` vía migración de esta spec, editable vía `PATCH /api/v1/productos/{sku}` ya existente en 001).

## Usuarios
- **Encargado de inventario:** consulta el stock actual global o por producto para decidir reposiciones. Único actor del MVP de consulta; sin autenticación ni roles en esta fase.

## Historias de usuario
- **HU-1:** Como encargado, quiero consultar el stock actual de todos los productos activos con su stock mínimo y un flag de alerta para ver de un vistazo qué reponer.
- **HU-2:** Como encargado, quiero consultar el stock actual de un producto concreto por su código para verificar su disponibilidad y si está en alerta.

## Requisitos funcionales

### RF-1 — Consultar stock actual con alerta
El sistema debe permitir consultar el stock actual derivado por producto y el listado global, recalculado en cada consulta, con indicador de alerta.
- Definiciones: `stock_minimo` es columna nueva en `productos` (esta spec, `Integer NOT NULL DEFAULT 0`, `CHECK >=0 AND <=1_000_000`, `NULL` persistido como `0`); `stock_actual` se calcula como en `003` (`stock_inicial` fijo de `001` + `suma(entradas tipo 'entrada')` - `suma(salidas tipo 'salida')`, excluyendo `entrada_inicial` del doble conteo); `alerta` es booleano `true` si `stock_minimo > 0 y stock_actual < stock_minimo`, en caso contrario `false` (estricto `<`, `==` no dispara; `stock_minimo == 0` nunca alerta, `null`/ausente tratado como `0`).
- **Criterios de aceptación (EARS):**
  - Cuando el encargado consulte el stock global, el sistema deberá devolver todos los productos con `estado == activo` ordenados por `codigo` `ASC`, cada uno con `codigo`, `nombre`, `stock_inicial`, `stock_minimo`, `entradas`, `salidas`, `stock_actual` y `alerta`.
  - Cuando el encargado consulte el stock de un producto existente y `activo` por código normalizado (`trim` solo extremos + `mayúsculas`, sin colapsar internos), el sistema deberá devolver `codigo`, `nombre`, `stock_minimo`, `stock_inicial`, `entradas`, `salidas`, `stock_actual` y `alerta`.
  - Si el producto consultado no existe, el sistema deberá responder 404 `Producto no encontrado`; si existe pero está `inactivo`, el sistema deberá responder 404 (solo lectura de `activos`; a diferencia de `001/spec.md:38` que devuelve `200` para catálogo, stock solo expone `activos` para evitar reponer inactivos).
  - Si no hay productos `activos`, el sistema deberá devolver `[]`.
  - Mientras un producto no tenga movimientos, el sistema deberá devolver `stock_actual == stock_inicial` y `alerta` según `stock_minimo` (`0` → `false`, `10` con `inicial 5` → `true`).
  - Cuando `stock_minimo == 0` (o `null` persistido como `0`), el sistema deberá devolver `alerta == false` siempre, independientemente de `stock_actual` (incluso `0`).

## Requisitos no funcionales
- **RNF-1 — Solo lectura:** esta funcionalidad no crea, edita ni borra productos ni movimientos; solo los interpreta. `stock_minimo` se persiste en `productos` pero se edita exclusivamente vía `PATCH /api/v1/productos/{sku}` (extendido en esta spec para aceptar `stock_minimo`).
- **RNF-2 — Reutilización de cálculo:** el stock actual reutiliza el mismo cálculo de `003` (`inicial + entradas - salidas`, sin `entrada_inicial`) implementado una sola vez en `services` y compartido entre `003` y `004` para evitar divergencia (principio 3).
- **RNF-3 — Desempeño de consulta:** el listado global recalcula el stock para todos los `activos` en una sola consulta agregada (`GROUP BY`); sin paginación en MVP pero con `ORDER BY codigo ASC` determinista, preparado para añadir `?limit&offset` sin breaking change.
- **RNF-4 — Validación y mensajes:** toda violación (código inexistente/inactivo) se rechaza sin efecto y con mensaje claro en español; validación de `codigo` es sintáctica (`trim+mayúsculas` `^[A-Z0-9_-]{3,20}$`) en `schemas`.
- **RNF-5 — Trazabilidad de mínimo:** `stock_minimo` se define una vez en `productos` y se lee en cada consulta; no se versiona histórico de cambios de mínimo en MVP.

## Casos límite
- Producto sin movimientos con `stock_inicial 5` y `stock_minimo 10` → `5` y `true`; con `stock_inicial 0` y `stock_minimo 0` → `0` y `false`.
- Producto con `stock_actual == stock_minimo` (5/5) → `false` (solo `<`); con `0` y `mínimo 5` → `true`.
- Producto con `stock_inicial 5` + `entrada 10` - `salida 3` = `12` y `stock_minimo 10` → `false`; con `salida 5` deja `7` con `mínimo 10` → `true`.
- Producto con `stock_minimo` `null` persistido como `0` → `false` siempre; con `stock_minimo` `0` explícito → `false`.
- Producto con `stock_inicial` `1_000_000` + `entrada` `1_000_000` → `2_000_000` permitido (límite es por movimiento, no por acumulado); `stock_minimo` `1_000_000` con `stock_actual` `2_000_000` → `false`.
- Consulta por código con espacios/`lowercase` (`  prod-001 `), `%2B`, `AB 01` con espacio interno → normaliza y `404` si no existe; `inactivo` → `404` en stock aunque `001` lo devolvería `200`.
- Consulta global con `0` activos y `5` `inactivos` con stock → `[]`; con `1k` activos sin paginación debe responder <500ms (ver RNF-3).
- `stock_minimo` con `""`/`1`/`>1_000_000`/`"-5"` enviado vía `PATCH /productos` → `422`; `null`/`ausente` en `POST /productos` → `0`.

## Fuera de alcance
- Creación, edición o borrado de movimientos o de `stock_actual` directo (esto es de `003`); `stock_actual` no se persiste, solo se deriva.
- Edición de `stock_minimo` desde esta vista de consulta (se hace vía `PATCH /api/v1/productos/{sku}` extendido en esta spec, pero la lógica de validación sigue en `001`).
- Filtros por `alerta=true`, por categoría, paginación u ordenamiento distinto a `codigo ASC`, y `?incluir_inactivos` (stock global siempre solo `activos` en MVP).
- Alertas push, notificaciones, reportes agregados o valores económicos.
- Autenticación, autorización y roles.

## Criterios de finalización
- RF-1 implementado y verificado según sus criterios EARS.
- `stock_actual` recalculado como en `003` (`inicial + entradas - salidas` sin `entrada_inicial`) y `alerta` como `stock_minimo >0 && stock_actual < stock_minimo` verificado para `0`, `==mínimo`, `<mínimo`, `>mínimo` y sin movimientos, con `stock_minimo` `0`/`null` → `false`.
- Listado global devuelve solo `activos` ordenados `codigo ASC` con `stock_minimo` y `alerta`; detalle por código normalizado devuelve `activo` con `alerta` y `404` para inexistente/inactivo.
- `stock_minimo` persistido como `0` por defecto, validado `0..1_000_000` y `null`/`""` según `001` extendido, y leído por `004` sin duplicar lógica de cálculo (servicio compartido).
- Todos los errores se rechazan sin efecto y con mensaje claro en español.
- Spec aprobada sin dudas bloqueantes y lista para implementación.

## Dudas abiertas
- Ninguna bloqueante para MVP. Futuras iteraciones evaluarán `?alerta=true` y paginación para el listado global.
