# Spec 012 — Registro de Ventas

## Contexto y objetivo
La tienda necesita registrar ventas que descuenten stock de forma trazable y atómica, reutilizando la lógica ya validada de salidas de stock. Hasta ahora, los movimientos de inventario (`003-movimientos-inventario`) permiten registrar entradas y salidas por producto individual, y la consulta de stock (`004`) deriva el estado, pero no existe una operación de negocio que agrupe varios productos en una sola venta con cliente y total, ni que garantice que el descuento de todos los ítems ocurra o ninguno ocurra.

Esta funcionalidad introduce el registro de ventas como operación de alto nivel: un carrito con varios productos distintos, cada uno con cantidad y precio unitario, asociado a un cliente embebido y a un total derivado, que al confirmarse genera una salida de stock por cada producto reutilizando estrictamente el service de `003` — nunca reimplementando el descuento. Toda la operación (venta + N salidas) es atómica: si un solo producto no tiene stock suficiente, toda la venta se rechaza sin descontar stock de ningún otro.

Desde `011-autenticacion`, todo endpoint requiere `Bearer` válido; ventas sigue esa regla sin introducir roles: cualquier usuario autenticado puede vender y consultar ventas. La venta es `append-only` como los movimientos: no se edita ni borra.

## Impacto en specs existentes
`003-movimientos-inventario` no se modifica, se **reutiliza** vía su service (`registrar_salida` con `SELECT FOR UPDATE` y validación de `stock_actual >= cantidad`). `011-autenticacion` impone que `POST` y `GET` de ventas exijan `Bearer` y respondan `401` sin él.

## Usuarios
- **Encargado de tienda / Vendedor** — mismo actor de `001`/`002`/`003`/`004`/`011`. Ahora autenticado, registra ventas con carrito y consulta historial de ventas. Percibe la venta como una sola operación que descuenta varios productos a la vez.
- **Cliente de la venta (actor indirecto, embebido)** — persona a la que se vende. No es usuario del sistema ni entidad reutilizable en este MVP; sus datos viven solo dentro de la venta.

## Historias de usuario
- **HU-1:** Como vendedor, quiero registrar una venta con varios productos (cantidad + precio unitario) y cliente, para que quede trazada y descuente stock atómicamente.
- **HU-2:** Como vendedor, quiero que si un producto del carrito no tiene stock suficiente, toda la venta se rechace sin descontar stock de ningún otro, para evitar ventas parciales inconsistentes.
- **HU-3:** Como vendedor, quiero consultar el listado de ventas en orden cronológico para auditar lo vendido.
- **HU-4:** Como vendedor, quiero consultar el detalle de una venta por su id para ver cliente, ítems, total y qué movimientos de salida originó.
- **HU-5:** Como vendedor, quiero recibir errores claros en español que indiquen qué producto del carrito falló y por qué (no encontrado, inactivo, stock insuficiente, validación), sin exponer detalles internos de `003`.

## Requisitos funcionales

### RF-1 — Registrar venta con carrito y cliente embebido
El sistema debe permitir registrar una venta con cliente embebido y carrito de 1 a 20 productos distintos, cada uno con cantidad y precio unitario, calculando subtotales y total de forma derivada.
- **Definiciones:** `cliente` embebido en la venta, sin tabla separada: `nombre` obligatorio tras `trim` 2-100 caracteres (misma regla de `001`/`002`), `email` opcional: `""` (vacío tras trim) → `422`, `null` o ausente → sin email (mismo criterio que `002`), si se informa debe cumplir mismo formato `002` (`local@dominio.tld`, `TLD>=2`, `≤254`, sin espacios); sin teléfono/dirección/identificador fiscal. `items` array 1-20 elementos, cada uno con `producto_codigo` que se normaliza (`trim+mayúsculas`) **antes** de validar formato `^[A-Z0-9_-]{3,20}$`, `cantidad` debe ser un entero en el JSON `1..1_000_000` — cualquier valor con parte decimal en su representación (ej. `2.00`, `2.5`) se rechaza con `422` por tipo, sin importar si el valor resultante sería entero (mismo criterio que `003` para cantidad como string `"2"`), `precio_unitario` `Decimal` `0.00..1_000_000.00` con máximo 2 decimales (`>2` decimales → `422`, con `0` o `1` decimal válido, nunca `float`), `subtotal` derivado `cantidad * precio_unitario` y `total` derivado `sum(subtotal)`. Si el cliente envía `total` o `subtotal` en el request, se ignoran silenciosamente sin validar ni rechazar — el backend siempre calcula y persiste los suyos, nunca se responde `422` por esto. `SKU` duplicado dentro del mismo carrito tras normalización es duplicado de negocio. `created_at` formato `ISO 8601 UTC` con sufijo `Z` (`YYYY-MM-DDTHH:MM:SSZ`), generado por el servidor, nunca enviado por el cliente. El service de ventas no expone ninguna operación de `UPDATE` ni `DELETE` sobre ventas (append-only, como `003`).
- **Orden de validación (resuelve contradicción 1 y ambigüedad 8):** en `POST /api/v1/ventas` el sistema valida en secuencia explícita: **(1)** toda validación de formato/estructura que no requiere base de datos — tamaño de carrito `1..20`, cliente `nombre`/`email`, `producto_codigo` formato tras normalización, `cantidad` tipo entero y rango, `precio_unitario` tipo y rango/decimales, `SKU` duplicado tras normalización — cualquier fallo aquí es `422`; **solo si esa etapa pasa completa**, **(2)** valida contra base de datos existencia de cada producto (`404` si no encontrado) y luego **(3)** estado activo y stock suficiente para cada ítem (`400` con detalle del producto). Esta secuencia define la prioridad de status si hay múltiples errores.
- **Criterios de aceptación (EARS):**
  - Cuando el vendedor solicite `POST /api/v1/ventas` con cliente válido, carrito 1-20 ítems con `producto_codigo`/`cantidad`/`precio_unitario` válidos, y todos los productos existen y están `activos`, y cada `cantidad ≤ stock_actual` (verificado por el service de ventas leyendo stock actual directamente, ver RF-2), el sistema deberá crear la venta con `id` autoincrement, `created_at` UTC con `Z`, `cliente` embebido, `items` con `subtotal`, `total` derivado y referencias a los `N` movimientos `salida` generados, y devolver `201` con el detalle completo.
  - Si el carrito está vacío, tiene 0 ítems o tiene más de 20 ítems, el sistema deberá rechazar con `422` y no crear venta ni movimientos.
  - Si algún ítem tiene `producto_codigo` con formato 3-20 inválido tras normalización, `cantidad` no entera/`0`/negativa/`>1_000_000`/string, `precio_unitario` negativo/`>1_000_000`/`>2` decimales/no numérico, o `SKU` duplicado tras normalización dentro del mismo carrito, el sistema deberá rechazar con `422` indicando el campo/ítem fallido y no crear venta ni movimientos.
  - Si `cliente.nombre` tras trim es vacío o viola 2-100, o `cliente.email` es `""` tras trim, o informado viola formato `002`, el sistema deberá rechazar con `422` y no crear venta; si `email` es `null` o ausente, el sistema deberá crear sin email.
  - Si `cliente` o `items` faltan o son `null`, el sistema deberá rechazar con `422`.
  - Si el cliente envía `total`, `subtotal`, `created_at` o `id` en el request, el sistema deberá ignorarlos silenciosamente sin validar ni rechazar, y siempre calcular y persistir los suyos.
  - Cuando la venta sea creada, el sistema deberá persistir `total` y cada `subtotal` como valores derivados `Decimal` y nunca recalcularlos a partir de un `total` enviado.

### RF-2 — Atomicidad y generación de salidas vía 003
El sistema debe garantizar que el registro de la venta y la generación de todas sus salidas de stock ocurran en una sola transacción atómica, reutilizando el service de `003` sin reimplementar el descuento.
- **Definiciones:** la validación de stock propia de ventas (existencia, estado activo y `cantidad ≤ stock_actual` leyendo stock actual directamente) la construye el propio service de ventas **antes** de invocar a `003`; el mensaje específico por producto (`código, disponible, solicitado`) lo construye ventas; `003` se invoca recién después de que todas las validaciones de venta ya pasaron, exclusivamente para ejecutar el descuento atómico ya autorizado.
- **Persistencia en caso de fallo:** si la venta se rechaza en cualquier etapa de validación (`422` de formato/estructura, `404` de no encontrado, `400` de inactivo o stock insuficiente), no se persiste absolutamente nada — ni venta, ni movimientos, ni `movimientos_ids`. La trazabilidad bidireccional (`RNF-3`) aplica únicamente a ventas creadas con éxito.
- **Criterios de aceptación (EARS):**
  - Cuando el vendedor solicite una venta válida, el sistema deberá, dentro de una única transacción, validar por sí mismo que todos los `producto_codigo` existen y están `activos`, y verificar que para cada ítem `cantidad ≤ stock_actual` leyendo el stock actual directamente (con `SELECT FOR UPDATE` para serializar concurrentes), y solo después invocar al service de `003` para crear `N` movimientos `salida` (uno por ítem); si todo valida, deberá hacer `commit` y devolver `201`.
  - Si cualquier ítem falla por `producto` no encontrado, el sistema deberá rechazar con `404` indicando el `producto_codigo` fallido y no crear venta ni ningún movimiento.
  - Si cualquier ítem falla por `producto` `inactivo`, el sistema deberá rechazar con `400` indicando el `producto_codigo` inactivo y no crear venta ni ningún movimiento.
  - Si cualquier ítem falla por `stock insuficiente` (`cantidad > stock_actual`), el sistema deberá rechazar con `400` específico de venta, indicando explícitamente el `producto_codigo` fallido, la cantidad disponible y la solicitada (ej. `Stock insuficiente para el producto X: disponible 3, solicitado 5`), y no crear venta ni ningún movimiento, sin descontar stock de los otros ítems.
  - El sistema nunca deberá dejar una venta a medias: o se crean la venta y los `N` movimientos, o no se crea nada (rollback total).
  - El sistema deberá reutilizar estrictamente el service de `003` para ejecutar cada salida ya validada (con `SELECT FOR UPDATE`); nunca deberá decrementar stock con `UPDATE` directo sin pasar por `003`.

### RF-3 — Consultar listado de ventas
El sistema debe permitir consultar el listado de ventas en orden cronológico, sin paginación en MVP, protegido con `Bearer`.
- **Criterios de aceptación (EARS):**
  - Cuando el vendedor solicite `GET /api/v1/ventas` (sin barra final, consistente con `/api/v1/movimientos`) con `Bearer` válido, el sistema deberá validar el `Bearer` **antes** de cualquier acceso a base de datos y, si es válido, devolver todas las ventas ordenadas por `created_at` descendente y desempate por `id` descendente, cada una con `id`, `created_at`, `cliente` (`nombre`, `email`), `items` (con `producto_codigo`, `cantidad`, `precio_unitario`, `subtotal`), `total` y `movimientos_ids` (IDs de las salidas generadas).
  - Si no hay ventas, el sistema deberá devolver `[]`.
  - Cuando el vendedor solicite `GET /api/v1/ventas` sin `Bearer` o con token inválido/expirado, el sistema deberá rechazar con `401` antes de cualquier acceso a BD, de forma idéntica a `011`.
  - El sistema no deberá exponer `password` ni `password_hash` ni detalles internos de movimientos más allá de sus IDs en el listado.

### RF-4 — Consultar detalle de venta por id
El sistema debe permitir consultar el detalle de una venta por su `id`, protegido con `Bearer`.
- **Criterios de aceptación (EARS):**
  - Cuando el vendedor solicite `GET /api/v1/ventas/{id}` con `Bearer` válido y el `id` existe, el sistema deberá validar el `Bearer` antes de cualquier acceso a BD y devolver la venta completa con `id`, `created_at`, `cliente`, `items` con `subtotal`, `total` y `movimientos_ids`.
  - Si el `id` no existe, el sistema deberá responder `404`.
  - Si la solicitud no lleva `Bearer` válido, el sistema deberá responder `401` antes de cualquier acceso a BD.
  - El sistema deberá garantizar que el `total` y los `subtotal` del detalle coinciden con los calculados al crear y que los `movimientos_ids` referencian movimientos `salida` existentes en el historial de `003`.

## Requisitos no funcionales
- **RNF-1 — Reutilización estricta de 003:** el descuento de stock de cada ítem delega al service de `003` (`registrar_salida`) con `SELECT FOR UPDATE`; no se duplica lógica de validación de `activo` ni de `stock_actual >= cantidad`. Verificación: inspección de `services` y tests de atomicidad.
- **RNF-2 — Atomicidad transaccional:** venta + N salidas en una sola transacción `BEGIN`/`COMMIT` con `rollback` total si un ítem falla; nunca deja stock descontado parcialmente. Verificación: tests de venta con stock insuficiente en un ítem y verificación de que `stock_actual` de los otros no cambió.
- **RNF-3 — Append-only y trazabilidad bidireccional:** ventas y movimientos nunca se editan ni borran (el service de ventas no expone `UPDATE`/`DELETE`); cada venta guarda `movimientos_ids` y cada movimiento `salida` generado queda en el historial de `003` consultable por `GET /movimientos`. Verificación: `GET /movimientos` contiene las salidas con `motivo` derivado de la venta y `GET /ventas/{id}` contiene sus IDs. Solo aplica a ventas creadas con éxito.
- **RNF-4 — Validación y mensajes en español:** toda violación se rechaza sin efecto colateral y con mensaje claro en español, indicando el `producto_codigo` fallido cuando aplica (stock insuficiente, no encontrado, inactivo, duplicado en carrito). Verificación: pruebas de validación.
- **RNF-5 — Autenticación obligatoria desde 011:** `POST` y `GET` de ventas exigen `Bearer` válido y responden `401` sin él; todo usuario autenticado puede vender (sin roles). Verificación: `TestClient` sin `Authorization` → `401`.
- **RNF-6 — Cálculo derivado con Decimal:** `precio_unitario`, `subtotal` y `total` usan `Decimal` con 2 decimales, nunca `float`, para evitar errores de redondeo. Verificación: `total == sum(cantidad*precio_unitario)` exacto con `Decimal` y validación en schemas Pydantic con `Decimal` (nunca `float`).
- **RNF-7 — Idioma:** mensajes visibles y de error siguen en español.
- **RNF-8 — Herencia de limitación de rate limiting:** `012` hereda la misma limitación de ausencia de rate limiting ya aceptada en `011` — no hay protección adicional contra envíos masivos de `POST /ventas` en este MVP. Verificación: revisión de `011` RNF-5.

## Casos límite
- Carrito vacío `[]` o `items: null` o ausente → `422`; carrito con 1 ítem válido → `201`; con 20 ítems válidos → `201`; con 21 → `422`.
- Carrito con `SKU` duplicado (mismo código normalizado `PROD-001` y ` prod-001 `) → `422` con detalle del duplicado, sin venta.
- Ítem con `cantidad` `0`, `-1`, `1.5`, `"2"` (string), `2.00` (decimal con parte fraccional), `1_000_001` → `422`; con `precio` `-0.01`, `1_000_000.01`, `10.123` (3 decimales), `"10.00"` (string), `null` → `422`; con `precio` `0.00` exacto, `10.50` o `10.5` (1 decimal) → `201` con `subtotal` correspondiente; `precio` `10` (sin decimales) → `201`.
- Producto inexistente en carrito → `404` con `producto_codigo` fallido, sin venta ni movimientos.
- Producto `inactivo` en carrito (aunque tenga stock) → `400` con `producto_codigo` inactivo, sin venta.
- Stock insuficiente en un ítem del carrito con varios productos (ej. `PROD-A` stock 10 pide 5 OK, `PROD-B` stock 3 pide 5 falla) → `400` específico `Stock insuficiente para PROD-B: disponible 3, solicitado 5`, sin venta y sin descuento de `PROD-A` (verificado leyendo `stock_actual` de `PROD-A` antes y después).
- Concurrencia: dos ventas simultáneas que individualmente tienen stock pero juntas lo exceden para el mismo `SKU` (stock 10, venta A pide 6 y venta B pide 6 concurrentes con `SELECT FOR UPDATE`) → una `201`, la otra `400` sin dejar stock negativo.
- Cliente con `nombre` `1` caracter o `101` o solo espacios → `422`; con `email` `sinarroba` o `""` → `422`; con `email` `null`/ausente → `201` con `email: null`; con `nombre` `  Ana  ` → `201` con `nombre` trim `Ana`.
- Venta con `total` enviado por cliente (`"total": 1.00` manipulado) o `subtotal`/`created_at`/`id` → ignorados silenciosamente, se persiste el derivado y el detalle devuelve el derivado, no el enviado, sin `422`.
- `GET /ventas` sin ventas → `[]`; con 3 ventas creadas en orden → `GET` devuelve orden `created_at DESC, id DESC`.
- `GET /ventas/{id}` con `id` inexistente → `404`; con `id` existente y token válido → `200` con `movimientos_ids` que existen en `GET /movimientos`.
- Solicitud sin `Bearer` o con `Bearer ` vacío/`Basic`/firma alterada/`exp` expirado → `401` antes de cualquier `SELECT` o `SELECT FOR UPDATE` (validación de token antes de BD, como en `011`).

## Fuera de alcance
- Cancelación o devolución de venta y reversión de stock; edición o borrado de venta (venta es `append-only`).
- Descuentos, impuestos, propinas, redondeos fiscales y métodos/procesamiento de pago.
- Reservas o apartados de stock y bloqueo preventivo fuera de la transacción de venta.
- Reutilización de cliente entre ventas y CRUD de clientes; el cliente es embebido y no reutilizable (sin tabla `clientes`).
- Campos adicionales de cliente (`teléfono`, `dirección`, `identificador fiscal`, `avatar`) y de venta (`notas`, `vendedor`, `caja`).
- Roles y permisos diferenciados para vender/consultar; todo autenticado puede vender.
- Paginación, filtros por cliente/fecha/rango de total, ordenamiento distinto a `created_at DESC, id DESC`, y reportes agregados.
- Valorización económica histórica, lotes, caducidad, ubicaciones de almacén y stock por almacén.
- Auditoría de quién realizó cada venta más allá del token (trazabilidad por usuario) — fuera de `011`.

## Criterios de finalización
- RF-1 a RF-4 implementados y verificados según sus criterios EARS: `POST /ventas` con cliente `nombre` 2-100 + `email` opcional formato `002` (`""`→`422`, `null`/ausente→`null`), carrito 1-20 ítems con `cantidad` entera `1..1_000_000` (con parte decimal →`422`) y `precio` `Decimal 0.00..1_000_000.00` (`>2` decimales→`422`, `0`/`1` decimal válido), `SKU` duplicado tras normalización → `422`, `total`/`subtotal`/`created_at` derivados/generados por servidor (enviados se ignoran), `201` con referencias a `N` movimientos; `GET /ventas` y `GET /ventas/{id}` protegidos con `Bearer` y validación antes de BD, orden `created_at DESC, id DESC`, `404` si `id` no existe, `401` sin token.
- RF-2 atomicidad verificada: venta con un ítem sin stock → `400` específico sin crear venta ni ningún movimiento, stock de los otros ítems sin cambios; concurrencia con `SELECT FOR UPDATE` de `003` deja una `201` y otra `400` sin `stock_actual <0`; si se rechaza en cualquier etapa `422/404/400` no se persiste nada.
- Reutilización estricta de `003` para cada salida: validación de existencia/activo/stock la hace ventas por sí misma leyendo stock actual directamente antes de invocar `003`, y `003` solo ejecuta el descuento atómico ya autorizado (sin `UPDATE` directo de stock) y trazabilidad bidireccional `venta.movimientos_ids` ↔ `movimientos` historial.
- Validaciones de carrito (vacío, >20, `cantidad`/`precio` rangos/decimales/string, duplicado) cubiertas con `422` y sin efecto; `null`/ausente vs `""` para cliente según `RF-1`.
- `POST` y `GET` de ventas exigen `Bearer` y responden `401` sin él, sin introducir roles; mensajes en español con `producto_codigo` fallido.
- `precio`/`total` con `Decimal` 2 decimales sin `float` (RNF-6); `stock_actual` nunca negativo; `created_at` `ISO 8601 UTC Z`.
- Todos los movimientos generados son `append-only` con `id`/`fecha` inmutables y `stock_actual` recalculado como en `003`; ventas sin `UPDATE`/`DELETE`.
- Spec aprobada sin [NECESITA ACLARACIÓN] bloqueante.

## Dudas abiertas
- Ninguna bloqueante para este MVP.
- [NECESITA ACLARACIÓN] Para specs futuros: si se introduce tabla `clientes` reutilizable, ¿debe migrar el `cliente` embebido de ventas históricas o mantenerse embebido por trazabilidad?
- [NECESITA ACLARACIÓN] Si se añade paginación a `GET /ventas`, ¿debe ser `limit/offset` o cursor por `created_at+id` para historial append-only?
