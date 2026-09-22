# Spec 003 — Movimientos de Inventario

## Contexto y objetivo
La tienda necesita registrar de forma fiable y auditable cada entrada y salida de stock para conocer el stock actual y su historial. Esta funcionalidad cubre el registro de movimientos (entrada asociada a proveedor y salida por venta/ajuste), su consulta histórica y el cálculo de stock actual derivado, garantizando unicidad de referencia a producto/proveedor, validación estricta de stock y trazabilidad permanente sin edición ni borrado, apoyándose en los catálogos de `001-productos` y `002-proveedores`. El stock actual se define como `stock_inicial` (valor fijo de `001`) + `suma(entradas tipo 'entrada')` - `suma(salidas)`; los movimientos `entrada_inicial` creados por `001` (tipo `entrada_inicial`) se muestran en el historial pero **no** se suman de nuevo para evitar doble conteo.

## Usuarios
- **Encargado de inventario:** registra entradas y salidas, consulta historial y stock actual. Único actor del MVP de movimientos; sin autenticación ni roles en esta fase.

## Historias de usuario
- **HU-1:** Como encargado, quiero registrar una entrada de stock para un producto activo indicando proveedor activo y cantidad, para que quede trazada y aumente el stock.
- **HU-2:** Como encargado, quiero registrar una salida de stock para un producto activo, para que quede trazada y disminuya el stock sin permitir negativo.
- **HU-3:** Como encargado, quiero consultar el historial de movimientos (global o por producto) ordenado cronológicamente para auditar entradas y salidas.
- **HU-4:** Como encargado, quiero consultar el stock actual de un producto (o de todos los activos) calculado como `inicial + entradas - salidas` para decidir reposiciones.

## Requisitos funcionales

### RF-1 — Registrar entrada de stock
El sistema debe permitir registrar una entrada con: `producto` (código SKU `trim` solo extremos + `mayúsculas`, sin colapsar internos, debe cumplir `^[A-Z0-9_-]{3,20}$`), `proveedor` (código `trim+mayúsculas` mismo formato), `cantidad` (entero `1` a `1_000_000`, sin decimales) y `motivo` opcional (`trim` 2-200 sin `\n`/`\r`/control, `null`/ausente no se valida, `""` tras trim → violación, con `Ñ`/`emoji` permitido si cumple longitud).
- **Criterios de aceptación (EARS):**
  - Cuando el encargado solicite una entrada con producto existente y `activo`, proveedor existente y `activo`, y cantidad válida, el sistema deberá crear el movimiento de tipo `entrada` con `id` autoincrement y `fecha` (`created_at` UTC generada por el sistema), incrementar el stock actual y devolver su identificador.
  - Si el producto no existe, el sistema deberá rechazar con error de no encontrado (404); si existe pero está `inactivo`, el sistema deberá rechazar con error de inactivo (400).
  - Si el proveedor no existe, el sistema deberá rechazar 404; si existe pero está `inactivo`, el sistema deberá rechazar 400. La validación de `producto`/`proveedor` se hace al inicio de la transacción con bloqueo pesimista para evitar carrera con baja concurrente.
  - Si la cantidad es `0`, negativa, decimal, no numérica o `>1_000_000`, el sistema deberá rechazar 422.
  - Si el motivo se informa con `""`, `1` o `201` caracteres, o con `\n`/`\r`, el sistema deberá rechazar 422; si es `null`/ausente, el sistema deberá crear sin motivo; con `2`/`200` exactos debe aceptarse y almacenarse `trim`.

### RF-2 — Registrar salida de stock
El sistema debe permitir registrar una salida con: `producto` (mismo formato y validación que RF-1), `cantidad` (`1` a `1_000_000`) y `motivo` opcional (mismas reglas que RF-1); **no** requiere `proveedor` y si se envía `proveedor` debe ignorarse o rechazarse con 422 (según capa de validación).
- **Criterios de aceptación (EARS):**
  - Cuando el encargado solicite una salida con producto activo, cantidad válida y stock suficiente (`stock_actual >= cantidad` verificado en `services` con `SELECT FOR UPDATE` del producto), el sistema deberá crear el movimiento de tipo `salida` y decrementar el stock.
  - Si el producto no existe → 404; si está `inactivo` → 400.
  - Si la cantidad es inválida (`0`, negativa, decimal, `>1_000_000`, `"10"` como string) → 422.
  - Si el stock actual es insuficiente (`cantidad > stock_actual`), el sistema deberá rechazar 400 stock insuficiente y no crear movimiento ni modificar el stock.
  - Si el motivo es `""`/`1`/`201`/`\n` → 422; `null`/ausente → acepta.

### RF-3 — Consultar historial de movimientos
El sistema debe permitir consultar el historial de movimientos, ordenado por `fecha` descendente y desempate por `id` descendente, con filtros opcionales por `producto` (`codigo` normalizado `trim+mayúsculas`) y `tipo` (`entrada`/`salida`/`entrada_inicial`); sin paginación en MVP (devuelve todo, ver RNF).
- **Criterios de aceptación (EARS):**
  - Cuando el encargado consulte el historial sin filtros, el sistema deberá devolver todos los movimientos (incluyendo `entrada_inicial` de `001`) con `id`, `producto` (codigo normalizado), `proveedor` (codigo o `null` para `salida`), `tipo`, `cantidad`, `motivo` y `fecha` (UTC ISO8601).
  - Cuando se filtre por `producto` con código normalizado, el sistema deberá devolver solo movimientos de ese producto; si el código no existe → 404; si el producto no tiene movimientos → `[]`.
  - Cuando se filtre por `tipo` con valor distinto a `entrada`/`salida`/`entrada_inicial` → 422; con valor válido debe filtrar exactamente ese tipo.
  - Si no hay movimientos, el sistema deberá devolver `[]`.

### RF-4 — Consultar stock actual
El sistema debe permitir consultar el stock actual derivado por producto y el listado global, recalculado en cada consulta desde la fuente append-only.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado consulte el stock de un producto existente por código normalizado, el sistema deberá devolver `codigo`, `nombre`, `stock_inicial`, `entradas` (suma de `entrada`), `salidas` (suma de `salida`), `entradas_iniciales` (opcional, solo informativo) y `stock_actual` (`stock_inicial + entradas - salidas`, sin sumar `entrada_inicial`).
  - Cuando se consulte el stock global sin parámetros, el sistema deberá devolver solo productos con `estado == activo` ordenados por `codigo`, cada uno con su `stock_actual`; incluir `inactivos` solo con flag `?incluir_inactivos=true` (por defecto solo activos). Si no hay productos activos → `[]`.
  - Mientras un producto no tenga movimientos, el sistema deberá devolver `stock_actual == stock_inicial`.
  - El sistema deberá recalcular el stock en cada consulta a partir de los movimientos registrados; `inactivo` permanece consultable pero no utilizable para nuevos movimientos (RNF-5).

## Requisitos no funcionales
- **RNF-1 — Integridad append-only:** ningún movimiento se edita ni borra; solo inserciones, con `id` autoincrement y `fecha` (`created_at`) inmutable generada por el sistema (UTC).
- **RNF-2 — Validación y mensajes:** toda violación se rechaza sin efecto colateral y con mensaje claro en español; validación sintáctica (`motivo`, `cantidad` formato) en `schemas` (400/422), validación de negocio (`producto`/`proveedor` activo, stock suficiente) en `services` (404/400).
- **RNF-3 — Consistencia de stock:** el stock actual es siempre `inicial + entradas - salidas`; una salida nunca deja `stock_actual < 0`; la verificación de stock insuficiente se hace con bloqueo pesimista (`SELECT FOR UPDATE` del producto) para garantizar serialización de salidas concurrentes.
- **RNF-4 — Trazabilidad:** cada `entrada` referencia a `proveedor` existente y `activo` al momento de creación (validado por `id`); cada movimiento referencia a `producto` existente y `activo` al momento; el historial conserva `codigo` (y `id`) aunque luego pasen a `inactivo`; `salida` con `proveedor` enviado debe ser ignorado.
- **RNF-5 — Prerrequisito:** `001` y `002` deben estar en `activo` para registrar movimientos; `inactivo` permanece consultable pero no utilizable para nuevos movimientos; `stock_actual` global por defecto solo `activos`.

## Casos límite
- Entrada con `proveedor` `inactivo`, inexistente, `__`, `--`, `*`, `ñ`, `emoji` o `codigo` `2`/`21` debe rechazarse; con `trim+mayúsculas` válido debe aceptarse.
- Entrada/salida con `producto` `inactivo`/inexistente, `lowercase`, `%2B`, `AB 01` debe rechazarse.
- Entrada/salida con `cantidad` `0`, `-1`, `1.5`, `"10"`, `1000001`, `1_000_000` límite debe comportarse según RF-1/2.
- Salida con `cantidad == stock_actual` debe dejar `0`; con `stock_actual+1` debe rechazar 400 sin movimiento; producto con `stock_inicial` `1_000_000` + `entrada` `1_000_000` → `stock_actual` `2_000_000` permitido (límite es por movimiento, no por acumulado).
- Entrada/salida con `motivo` `""`/`1`/`201`/`\n`/`Ñ`/`emoji`/`null`/ausente según RF-1.
- Concurrencia: dos `salida` simultáneas que individualmente tienen stock pero juntas lo exceden — una 200, la otra 400; dos `entrada` simultáneas con mismo `proveedor` activo que pasa a `inactivo` concurrente — entrada debe ver `proveedor` ya `inactivo` y rechazar 400.
- Historial con `producto` inexistente → 404 si se filtra por producto, `[]` si filtro no aplicado; `tipo` inválido → 422.
- Stock actual de producto sin movimientos → `stock_inicial`; con solo `entrada_inicial` → `stock_inicial` (no doble); con `inactivo` y stock>0 → consultable pero no permite nuevas salidas.

## Fuera de alcance
- Edición o borrado de movimientos ya registrados, incluso de su `motivo`.
- Valorización económica (costes, precios, totales), reservas, lotes, caducidad o ubicaciones de almacén.
- Reactivación de productos/proveedores inactivos, borrado físico y edición de `stock_inicial` directo (ya cubierto en `001`).
- Filtros avanzados por fecha, paginación, ordenamiento distinto a `fecha` desc + `id` desc y reportes agregados (historial devuelve todo sin paginación en MVP).
- Autenticación, autorización y roles.

## Criterios de finalización
- RF-1 a RF-4 implementados y verificados según sus criterios EARS.
- Validaciones de `producto`/`proveedor` `activo`, `cantidad` 1-1_000_000 entero y `motivo` 2-200 cubiertas con pruebas, incluyendo `null`/ausente vs `""`, `lowercase`/`trim` y `proveedor` `null` para salidas.
- Salida con stock insuficiente rechazada sin crear movimiento y sin dejar stock negativo, con bloqueo pesimista verificado en pruebas de concurrencia.
- Historial devuelve todos los movimientos con `proveedor` `null` para `salida` y `codigo` normalizado, ordenado `fecha` desc + `id` desc; stock actual recalculado como `inicial + entradas - salidas` (excluyendo `entrada_inicial` del `inicial`) y consistente con historial.
- Todos los movimientos son append-only con `id`/`fecha` inmutables; ningún `UPDATE`/`DELETE` sobre histórico; `stock_actual` global por defecto solo `activos`.
- Spec aprobada sin dudas bloqueantes y lista para implementación.

## Dudas abiertas
- Ninguna bloqueante para MVP. Futuras iteraciones evaluarán paginación por defecto para historial y si `proveedor` debe ser `id` o `codigo` en la API de movimientos (actualmente `codigo` en API, `id` en modelo).
