# Spec 001 — Catálogo de Productos

## Contexto y objetivo
La tienda necesita un catálogo fiable como base del inventario. Esta funcionalidad cubre exclusivamente el ciclo de vida del producto — alta, consulta, edición y baja lógica — para videojuegos, consolas y accesorios, garantizando unicidad y trazabilidad sin gestionar movimientos posteriores ni niveles de stock en el tiempo, que se abordan en specs separadas.

## Usuarios
- **Encargado de catálogo:** mantiene el catálogo al día. Único actor del MVP de catálogo; sin autenticación ni roles en esta fase.

## Historias de usuario
- **HU-1:** Como encargado, quiero dar de alta un producto con SKU, nombre, categoría y stock inicial para incorporarlo al catálogo.
- **HU-2:** Como encargado, quiero consultar el listado de productos activos para verificar el catálogo vigente.
- **HU-3:** Como encargado, quiero consultar el detalle de un producto por SKU, aunque esté dado de baja, para conservar trazabilidad.
- **HU-4:** Como encargado, quiero editar nombre y categoría de un producto activo para corregir datos sin cambiar su identidad.
- **HU-5:** Como encargado, quiero dar de baja lógica un producto para retirarlo del listado sin borrar su historial.

## Requisitos funcionales

### RF-1 — Alta de producto
El sistema debe permitir dar de alta un producto activo con: nombre, SKU, categoría y stock inicial.
- Definiciones: SKU tras normalización `trim + mayúsculas` debe tener 3-20 caracteres alfanuméricos, guion `-` o guion bajo `_`, único global incluyendo productos inactivos y no reutilizable; nombre tras `trim` 2-100 caracteres, no vacío ni solo espacios, permite duplicados con distinto SKU; categoría enum exacto `videojuego` | `consola` | `accesorio` tras `trim + minúsculas` (alias `juego` inválido); stock inicial opcional, si ausente o `null` equivale a 0, debe ser entero >=0 y <=1_000_000.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado solicite alta con nombre, SKU, categoría y stock inicial válidos y SKU normalizado no existente, el sistema deberá crear el producto en estado `activo`.
  - Si el SKU normalizado ya existe (activo o inactivo), el sistema deberá rechazar con error de duplicado y no crear el producto.
  - Si falta nombre, SKU o categoría, o cualquiera viola longitud/formato/enum, el sistema deberá rechazar con error de validación.
  - Si el stock inicial es negativo, decimal, no numérico o >1_000_000, el sistema deberá rechazar con error de validación.
  - Cuando el stock inicial sea >0, el sistema deberá registrar ese valor como stock inicial del producto y dejar traza append-only de entrada inicial por esa cantidad (única operación de movimiento permitida en este spec).

### RF-2 — Consulta de listado de productos
El sistema debe permitir consultar el listado de productos activos del catálogo (sin exponer stock actual dinámico).
- **Criterios de aceptación (EARS):**
  - Cuando el encargado consulte el listado, el sistema deberá devolver únicamente productos con estado `activo`, cada uno con `sku` (normalizado), `nombre`, `categoria` y `stock_inicial`.
  - Si no hay productos activos, el sistema deberá devolver lista vacía.
  - Mientras un producto esté `inactivo`, el sistema deberá excluirlo del listado.

### RF-3 — Consulta de detalle por SKU
El sistema debe permitir consultar el detalle de un producto por SKU, incluyendo inactivos para trazabilidad.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado consulte por SKU existente (activo o inactivo) usando valor normalizado, el sistema deberá devolver su detalle completo (`sku`, `nombre`, `categoria`, `stock_inicial`, `estado`).
  - Si el SKU normalizado no existe, el sistema deberá responder con error de no encontrado.
  - El sistema deberá aplicar la misma normalización de SKU que en el alta para la búsqueda.

### RF-4 — Edición de producto
El sistema debe permitir editar solo `nombre` y `categoria` de un producto activo; `sku` es inmutable y el stock no se edita por esta vía.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado edite un producto activo con `nombre` y/o `categoria` válidos, el sistema deberá actualizar solo esos campos.
  - Si el producto no existe (SKU normalizado no encontrado), el sistema deberá rechazar con error de no encontrado.
  - Si el producto está `inactivo`, el sistema deberá rechazar la edición con error de no editable.
  - Si el `nombre` tras trim es vacío o viola 2-100 caracteres, o la `categoria` no es del enum, el sistema deberá rechazar con error de validación.
  - Si la solicitud incluye campo `sku` con valor distinto al actual (tras normalización), el sistema deberá rechazar con error de inmutable; si incluye el mismo valor actual, el sistema deberá ignorarlo.

### RF-5 — Baja lógica de producto
El sistema debe permitir dar de baja lógica un producto activo sin borrarlo físicamente y sin validar su stock.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado solicite baja de un producto activo existente, el sistema deberá marcarlo como `inactivo` y conservarlo para historial.
  - Si el SKU no existe, el sistema deberá rechazar con error de no encontrado.
  - Si el producto ya está `inactivo`, el sistema deberá rechazar con error de ya dado de baja (no idempotente).
  - El sistema deberá permitir la baja independientemente del `stock_inicial`.

## Requisitos no funcionales
- **RNF-1 — Integridad append-only:** ningún producto ni traza de entrada inicial se borra físicamente; la baja es solo cambio de `estado` a `inactivo`.
- **RNF-2 — Validación y mensajes:** toda violación se rechaza sin efecto colateral y con mensaje de error claro en español.
- **RNF-3 — Unicidad permanente:** el SKU normalizado identifica unívocamente al producto durante todo su ciclo, incluso tras la baja, y no es reutilizable.
- **RNF-4 — Consistencia de consulta:** el listado refleja solo `activos`; el detalle refleja el estado real (`activo`/`inactivo`).
- **RNF-5 — Trazabilidad limitada:** el stock inicial >0 deja traza de entrada inicial inmutable; cualquier otro movimiento queda fuera de este spec.

## Casos límite
- Alta con SKU duplicado que difiere solo en mayúsculas, espacios o guiones debe rechazarse por normalización.
- Alta con SKU de 2 o 21 caracteres, con caracteres no permitidos (ej. `*`, ` `, `ñ`), o nombre de 1 o 101 caracteres debe rechazarse.
- Alta con `categoria` `Videojuego`, `CONSOLA`, `juego` o con tildes/espacios debe tratarse según normalización y rechazarse si no es enum exacto.
- Alta con `stock_inicial` `null`/ausente equivale a 0 y no genera traza; con `0` tampoco; con `>0` sí.
- Alta con `stock_inicial` decimal, string, negativo o >1_000_000 debe rechazarse.
- Alta con SKU de producto inactivo debe rechazarse (no reutilizable).
- Edición con payload vacío, sin cambios, o con campos extra (`stock`, `estado`) debe ignorar extras y validar solo `nombre`/`categoria`.
- Edición o baja concurrente del mismo SKU: una debe tener éxito, la otra recibir error de estado/no encontrado según orden.
- Consulta por SKU con espacios/mayúsculas debe resolver por normalización.

## Fuera de alcance
- Movimientos posteriores de entrada/salida, ajustes de stock y cálculo de stock actual dinámico.
- Consulta de niveles de stock en el tiempo, historial de movimientos y alertas de stock mínimo.
- Reactivación de productos inactivos, borrado físico y edición de SKU o de stock directo.
- Filtros avanzados, búsqueda por texto, paginación, ordenamiento y gestión de proveedores/ventas/reservas/precios.
- Autenticación, autorización y roles.

## Criterios de finalización
- RF-1 a RF-5 implementados y verificados según sus criterios EARS.
- Validaciones de longitud, formato, enum, rango y unicidad (incluyendo inactivos y normalización) cubiertas con pruebas.
- Listado devuelve solo activos; detalle por SKU devuelve activos e inactivos; baja oculta del listado sin borrar.
- Traza de entrada inicial creada solo cuando `stock_inicial >0` y nunca borrada/modificada.
- Todos los errores se rechazan sin efecto y con mensaje claro en español.
- Spec aprobada sin dudas bloqueantes.

## Dudas abiertas
- Ninguna bloqueante para este MVP. Futuras specs definirán gestión de movimientos y cálculo de stock actual.
