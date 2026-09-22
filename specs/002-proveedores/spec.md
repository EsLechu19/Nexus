# Spec 002 — Gestión de Proveedores

## Contexto y objetivo
La tienda necesita gestionar a los proveedores a los que compra productos para reponer stock. Sin un catálogo fiable de proveedores no se puede trazar el origen de las entradas de inventario. Esta funcionalidad cubre exclusivamente alta, consulta, edición y baja lógica de proveedores, garantizando unicidad y trazabilidad. Es prerrequisito de `003-movimientos-inventario`, ya que todo movimiento de entrada deberá referenciar obligatoriamente a un proveedor existente y en estado `activo`; los proveedores `inactivos` permanecen consultables pero no utilizables para nuevas entradas.

## Usuarios
- **Encargado de compras:** mantiene el catálogo de proveedores al día. Único actor del MVP de proveedores; sin autenticación ni roles en esta fase.

## Historias de usuario
- **HU-1:** Como encargado, quiero dar de alta un proveedor con código, nombre y contacto opcional para registrarlo como origen de compras.
- **HU-2:** Como encargado, quiero consultar el listado de proveedores activos para seleccionar a quién comprar.
- **HU-3:** Como encargado, quiero consultar el detalle de un proveedor por código, aunque esté dado de baja, para conservar trazabilidad.
- **HU-4:** Como encargado, quiero editar nombre y datos de contacto de un proveedor activo para corregir información sin cambiar su identidad.
- **HU-5:** Como encargado, quiero dar de baja lógica un proveedor para retirarlo del listado sin borrar su historial, aunque tenga movimientos previos.

## Requisitos funcionales

### RF-1 — Alta de proveedor
El sistema debe permitir dar de alta un proveedor activo con: código (obligatorio, único global e inmutable), nombre (obligatorio), y contacto opcional (email, teléfono, dirección).
- Definiciones: código tras normalización `trim` solo en extremos + `mayúsculas` debe cumplir `^[A-Z0-9_-]{3,20}$` (sin espacios internos, `_`/`-` permitidos en cualquier posición), único global incluyendo inactivos y no reutilizable; nombre tras `trim` solo extremos 2-100 caracteres, no vacío ni solo espacios, permite duplicados con distinto código y puede contener números/símbolos; email opcional, si se informa y no es `null` ni ausente, tras `trim + minúsculas` debe cumplir formato sintáctico `local@domino.tld` con 1 `@`, local 1-64, dominio con al menos un `.` y TLD >=2, sin espacios, longitud total <=254 (solo sintáctico, sin verificar dominio); teléfono opcional, si se informa y no es `null`/ausente, tras `trim` debe contener 7-15 dígitos; puede incluir `+` solo al inicio, espacios, guiones y paréntesis `()` como separadores, pero no letras; se contabilizan solo dígitos para el rango; se almacena conservando formato original; dirección opcional, si se informa y no es `null`/ausente, tras `trim` 5-200 caracteres imprimibles (sin caracteres de control); `""` tras trim se considera violación si el campo se envía, `null`/ausente se considera no informado y no se valida.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado solicite alta con código y nombre válidos y código normalizado no existente, el sistema deberá crear el proveedor en estado `activo`.
  - Si el código normalizado ya existe (activo o inactivo), el sistema deberá rechazar con error de duplicado y no crear el proveedor.
  - Si falta código o nombre, o cualquiera viola longitud/formato, el sistema deberá rechazar con error de validación.
  - Si email, teléfono o dirección se informan con valor no `null` y violan su formato/longitud, el sistema deberá rechazar con error de validación.
  - Si no se informa contacto (campos ausentes o `null`), el sistema deberá crear el proveedor sin validar contacto.

### RF-2 — Consulta de listado de proveedores
El sistema debe permitir consultar el listado de proveedores activos, ordenado por código.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado consulte el listado, el sistema deberá devolver únicamente proveedores con estado `activo`, cada uno con `codigo` (normalizado), `nombre`, `email`, `telefono` y `direccion` (sin `estado`, implícitamente `activo`).
  - Si no hay proveedores activos, el sistema deberá devolver lista vacía.
  - Mientras un proveedor esté `inactivo`, el sistema deberá excluirlo del listado.

### RF-3 — Consulta de detalle por código
El sistema debe permitir consultar el detalle de un proveedor por código, incluyendo inactivos para trazabilidad.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado consulte por código existente (activo o inactivo) usando valor normalizado, el sistema deberá devolver su detalle completo (`codigo`, `nombre`, `email`, `telefono`, `direccion`, `estado`).
  - Si el código normalizado no existe, el sistema deberá responder con error de no encontrado.
  - El sistema deberá aplicar la misma normalización de código (`trim + mayúsculas`, sin colapsar internos) que en el alta para la búsqueda.

### RF-4 — Edición de proveedor
El sistema debe permitir editar solo `nombre` y contacto (`email`, `telefono`, `direccion`) de un proveedor activo; `codigo` es inmutable y `estado` no se edita por esta vía.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado edite un proveedor activo con `nombre` y/o contacto válidos, el sistema deberá actualizar solo esos campos; `null` explícito para `email`/`telefono`/`direccion` deberá borrar el campo (poner `null`), campo ausente deberá dejarlo sin cambios, `""` tras trim deberá rechazarse como violación.
  - Si el proveedor no existe (código normalizado no encontrado), el sistema deberá rechazar con error de no encontrado.
  - Si el proveedor está `inactivo`, el sistema deberá rechazar la edición con error de no editable.
  - Si el `nombre` tras trim es vacío o viola 2-100, o `email`/`telefono`/`direccion` con valor no `null` violan formato/longitud, el sistema deberá rechazar con error de validación.
  - Si la solicitud no incluye ningún campo editable (`nombre`/`email`/`telefono`/`direccion`), el sistema deberá rechazar con error de payload vacío.
  - Si la solicitud incluye campo `codigo` con valor distinto al actual (tras normalización), el sistema deberá rechazar con error de inmutable; si incluye el mismo valor actual, el sistema deberá ignorarlo.
  - Si la solicitud incluye `estado`, el sistema deberá ignorarlo.

### RF-5 — Baja lógica de proveedor
El sistema debe permitir dar de baja lógica un proveedor activo sin borrarlo físicamente y sin validar movimientos previos, pero inhabilitándolo para futuras entradas.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado solicite baja de un proveedor activo existente, el sistema deberá marcarlo como `inactivo` y conservarlo para historial.
  - Si el código no existe, el sistema deberá rechazar con error de no encontrado.
  - Si el proveedor ya está `inactivo`, el sistema deberá rechazar con error de ya dado de baja (no idempotente).
  - El sistema deberá permitir la baja independientemente de que existan movimientos de entrada asociados; tras la baja, `003-movimientos-inventario` deberá rechazar nuevas entradas que referencien a ese proveedor por estar `inactivo`, pero el proveedor seguirá siendo consultable por detalle para trazabilidad.

## Requisitos no funcionales
- **RNF-1 — Integridad append-only:** ningún proveedor se borra físicamente; la baja es solo cambio de `estado` a `inactivo`; el historial y los movimientos previos que lo referencian permanecen intactos (referencia por id, no por snapshot de contacto).
- **RNF-2 — Validación y mensajes:** toda violación se rechaza sin efecto colateral y con mensaje de error claro en español; la validación de `email`/`telefono` es solo sintáctica en `schemas` (capa de interfaz), no requiere I/O ni verifica dominio/operador.
- **RNF-3 — Unicidad permanente:** el código normalizado identifica unívocamente al proveedor durante todo su ciclo, incluso tras la baja, y no es reutilizable.
- **RNF-4 — Consistencia de consulta:** el listado refleja solo `activos` (sin campo `estado`); el detalle refleja el estado real (`activo`/`inactivo`).
- **RNF-5 — Prerrequisito trazable:** todo proveedor permanece consultable por código tras la baja; `003-movimientos-inventario` validará que el proveedor referenciado exista y esté `activo`.

## Casos límite
- Alta con código duplicado que difiere solo en mayúsculas, espacios extremos o `_-` debe rechazarse por normalización; código con `__`, `--`, espacios internos, `*`, `ñ`, emoji o 2/21 caracteres debe rechazarse.
- Alta con nombre de 2/100 exactos debe aceptarse; con 1/101 o solo espacios debe rechazarse; nombre duplicado con distinto código debe aceptarse.
- Alta con email sin `@`, sin punto en dominio, con espacios, de 255 caracteres, o `""` debe rechazarse; con mayúsculas debe normalizarse a minúsculas y aceptarse; `null`/ausente debe aceptarse.
- Alta con teléfono con 6 dígitos, 16 dígitos, letras, `+` en medio, o solo `+`/guiones sin 7 dígitos debe rechazarse; con `+` al inicio, espacios, guiones o `()` y 7-15 dígitos debe aceptarse.
- Alta con dirección de 5/200 exactos debe aceptarse; con 4/201, con `\n` de control o `""` debe rechazarse; `null`/ausente debe aceptarse.
- Concurrencia: dos altas simultáneas con mismo código normalizado — una debe tener éxito, la otra 409.
- Edición que envía `{"email": null}` debe borrar email; que omite `email` debe dejarlo igual; que envía `{"email": ""}` debe rechazarse; payload vacío `{}` debe rechazarse.
- Baja concurrente del mismo código — una 200, la otra 400 ya dado de baja.
- Consulta por código con `%2B`, espacios, `lowercase` debe resolver por normalización.

## Fuera de alcance
- Gestión de movimientos de inventario (entradas/salidas), validación de stock y referencia obligatoria a proveedor en entradas (será `003-movimientos-inventario`, que exigirá proveedor `activo`).
- Gestión de productos, categorías, stock actual y alertas.
- Reactivación de proveedores inactivos, borrado físico y edición de código o de estado directo.
- Filtros avanzados, búsqueda por texto, paginación, ordenamiento.
- Gestión de compras, facturas, precios y pagos a proveedores.
- Autenticación, autorización y roles.

## Criterios de finalización
- RF-1 a RF-5 implementados y verificados según sus criterios EARS.
- Validaciones de longitud, formato y unicidad (incluyendo inactivos y normalización) cubiertas con pruebas para código, nombre, email, teléfono y dirección, incluyendo `null`/ausente vs `""` y borrado vía `null`.
- Listado devuelve solo activos sin campo `estado`; detalle por código devuelve activos e inactivos con `estado`; baja oculta del listado sin borrar y permite baja aunque existan movimientos previos, pero inhabilita para futuras entradas en `003`.
- Todos los errores se rechazan sin efecto y con mensaje claro en español.
- Spec aprobada sin dudas bloqueantes y lista para servir como prerrequisito de `003-movimientos-inventario`.

## Dudas abiertas
- [NECESITA ACLARACIÓN] ¿Se permitirá en el futuro reactivar un proveedor dado de baja o la baja es definitiva?
