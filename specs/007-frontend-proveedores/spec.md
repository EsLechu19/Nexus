# Spec 007 — Frontend Proveedores (Gestión de Catálogo)

## Contexto y objetivo
La tienda necesita gestionar su catálogo de proveedores desde la interfaz web, apoyándose en el mismo patrón validado en `006-frontend-productos` (listado + modal de formulario + confirmación de baja) y en el esqueleto base de `005-frontend-base` (layout, cliente API centralizado y componentes base de cargando/error/vacío). Esta funcionalidad entrega exclusivamente la pantalla de proveedores que consume el backend definido en `002-proveedores` (alta con código/nombre/contacto opcional, listado de activos ordenado por código, edición de nombre/contacto y baja lógica), sin incluir movimientos de inventario ni validación de stock. Es prerrequisito de `003-movimientos-inventario`, ya que las entradas deberán referenciar un proveedor activo.

## Usuarios
- **Encargado de compras:** mantiene el catálogo de proveedores al día (único actor del MVP). Sin autenticación ni roles; mismo operador de tienda de `005`/`006`.

## Historias de usuario
- **HU-1:** Como encargado, quiero ver el listado de proveedores activos con su código, nombre y contacto para seleccionar a quién comprar.
- **HU-2:** Como encargado, quiero crear un proveedor nuevo indicando código, nombre y contacto opcional para registrarlo como origen de compras.
- **HU-3:** Como encargado, quiero editar el nombre y los datos de contacto de un proveedor activo para corregir información sin cambiar su identidad.
- **HU-4:** Como encargado, quiero dar de baja lógica un proveedor activo para retirarlo del listado sin borrar su historial, aunque tenga movimientos previos.
- **HU-5:** Como encargado, quiero entender qué pasó cuando una operación falla para corregir o reintentar sin perder contexto.

## Requisitos funcionales

### RF-1 — Listado de proveedores activos
El sistema debe mostrar el listado de proveedores activos ordenado por código, con cinco columnas fijas y estados uniformes reutilizados de `005`.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado acceda a la sección proveedores, el sistema deberá pedir el listado a la API y mostrar cada proveedor con `codigo` (normalizado), `nombre`, `email`, `telefono` y `direccion` en una tabla sin filtros, sin ordenamiento en el frontend y sin paginación; la foto completa es tal cual la devuelve la API ordenada por `codigo` (el backend garantiza el orden, el frontend solo lo muestra sin reordenar), con scroll vertical si crece y sin truncar.
  - Mientras se espera la respuesta, el sistema deberá mostrar el estado cargando uniforme con texto "Cargando...".
  - Cuando la API devuelva lista vacía, el sistema deberá mostrar el estado vacío con mensaje "Sin datos disponibles".
  - Cuando la API responda con error 4xx, el sistema deberá mostrar el mensaje específico devuelto por la API sin botón Reintentar; cuando sea error de red, timeout o 5xx, deberá mostrar "Error de conexión con el servidor" con botón "Reintentar" que reejecute solo la carga del listado.
  - Cuando `email`, `telefono` o `direccion` sean `null` en la respuesta, el sistema deberá mostrar un guion "—" en esa celda de la tabla; en el formulario de edición esos `null` se precargarán como campo vacío `""` (no como literal "—") para permitir edición, y el literal "—" solo existe en la tabla.
  - El sistema no deberá mostrar columna de estado, ya que el listado solo contiene activos por contrato de `002`; la trazabilidad de inactivos permanece disponible vía `GET /proveedores/{codigo}` en la API pero no se muestra en esta pantalla.

### RF-2 — Alta de proveedor
El sistema debe permitir crear un proveedor mediante formulario modal dentro de la pantalla de listado.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado accione "Crear proveedor", el sistema deberá abrir un formulario modal con campos `codigo` (texto requerido), `nombre` (texto requerido), `email` (texto opcional), `telefono` (texto opcional) y `direccion` (texto opcional).
  - Si `codigo` o `nombre` están vacíos tras `trim` (incluye `"   "` solo espacios), o si `email`/`telefono`/`direccion` se informan y quedan vacíos tras `trim` (ej. `"   "`), el sistema deberá señalar error de forma "Campo requerido" o "No puede quedar vacío" sin llamar a la API; el frontend valida solo presencia tras `trim` (si opcional queda `""` tras trim se bloquea), no valida duplicidad de código, longitudes, formatos de `email`/`telefono`/`direccion` (ej. `"a@b"`, `"123"`) — esas reglas las decide el backend y el mensaje 4xx se muestra tal cual.
  - Cuando el encargado envíe el formulario con forma válida, el sistema deberá enviar la creación a la API y deshabilitar el botón de envío mientras la petición está en curso.
  - Si la API responde con error 4xx (ej. código duplicado normalizado con `trim+mayúsculas` sin colapsar internos, longitud/formato inválido de código/nombre/email/teléfono/dirección), el sistema deberá mantener el modal abierto y mostrar el mensaje específico devuelto por la API sin reintento automático.
  - Si la API responde con error de red, timeout o 5xx, el sistema deberá mantener el modal abierto y mostrar "Error de conexión con el servidor" con Reintentar que reejecute solo el alta.
  - Cuando la API confirme alta exitosa, el sistema deberá cerrar el modal, mostrar mensaje breve "Proveedor creado correctamente" como banner dentro de la pantalla sobre la tabla (con `role="status"` `aria-live="polite"`, visible 3 segundos, distinto de `ErrorMessage`), y revalidar el listado pidiéndolo de nuevo a la API (sin persistencia en cliente); si la revalidación posterior falla, se mantendrá el banner de éxito visible sus 3s y además se mostrará el error del listado con Reintentar (ambos coexisten).

### RF-3 — Edición de proveedor activo
El sistema debe permitir editar nombre y contacto de un proveedor activo reutilizando el mismo formulario modal, con semántica de borrado vía `null`.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado accione "Editar" en la fila de un proveedor activo, el sistema deberá abrir el modal con `codigo` visible pero deshabilitado (solo lectura, no se envía en el payload), y `nombre`, `email`, `telefono`, `direccion` precargados; si son `null` en la API se precargan como vacío `""` en el input (no como "—"); `codigo` no se edita.
  - Si el proveedor está inactivo, el sistema no lo mostrará en el listado (por `002` RF-2); el botón Editar deshabilitado/oculto para inactivos es defensivo para carrera (ej. otro usuario lo dio de baja entre carga y clic) — en flujo normal no se alcanza y nunca se ve un inactivo para editar.
  - Para distinguir intención en contacto opcional: si el usuario deja el campo sin tocar (ausente) no se envía; si borra el contenido y lo deja vacío `""` tras `trim`, el sistema deberá bloquearlo localmente como error de forma; si activa la acción explícita "Borrar" (ej. botón limpiar junto al input) el sistema deberá enviar `null` para borrar; si escribe un valor no vacío se envía tal cual.
  - Si el encargado deja `nombre` vacío tras `trim`, o informa `email`/`telefono`/`direccion` que queda `""` tras `trim`, el sistema deberá señalar error de forma sin llamar a la API; enviar `null` explícito para borrar es válido.
  - Si el payload resulta vacío (ningún campo editable con intención de cambio: `nombre` sin cambios y contacto todo ausente/sin tocar), el sistema deberá señalar error local "Sin cambios para guardar" sin llamar a la API (esto es UX forma, aunque el backend también rechaza `{}` con 4xx, el frontend lo evita para no duplicar llamada).
  - Cuando el encargado envíe cambios válidos, el sistema deberá enviar a la API solo los campos con intención: `nombre` si cambió, y para contacto `email`/`telefono`/`direccion` con `null` para borrar, con valor para actualizar, u omitido para conservar; nunca enviar `codigo` ni `estado`; deshabilitar botón mientras la petición está en curso.
  - Si la API responde con error 4xx (ej. nombre inválido, email/teléfono/dirección con formato/longitud inválida, `""` tras trim, payload vacío, proveedor ya inactivo o no encontrado por concurrencia), el sistema deberá mantener el modal abierto y mostrar el mensaje específico de la API sin reintento.
  - Si la API responde con error de red/timeout/5xx, el sistema deberá mantener el modal abierto y mostrar "Error de conexión con el servidor" con Reintentar.
  - Cuando la API confirme edición exitosa, el sistema deberá cerrar el modal, mostrar "Proveedor actualizado correctamente" (banner 3s `role="status"`) y revalidar el listado; si la revalidación falla, mostrar error de listado además del éxito.

### RF-4 — Baja lógica de proveedor
El sistema debe permitir dar de baja lógica un proveedor activo con confirmación explícita, aunque tenga movimientos previos.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado accione "Dar de baja" en la fila de un proveedor activo, el sistema deberá abrir un diálogo de confirmación con texto "¿Dar de baja a <nombre> (<codigo>)? No se puede deshacer desde este MVP" y opciones Confirmar/Cancelar, con foco inicial en Cancelar.
  - Si el encargado cancela o cierra el diálogo con ESC/navegación mientras no hay petición en curso, el sistema deberá cerrar el diálogo sin efecto; si hay petición en curso, ESC y navegación se ignoran y la petición se mantiene en curso sin cancelarse, sin deshabilitar navegación global.
  - Si el encargado confirma, el sistema deberá enviar la baja a la API y deshabilitar el botón Confirmar mientras la petición está en curso.
  - Si la API responde con error 4xx (ej. código no encontrado o ya dado de baja por concurrencia), el sistema deberá mostrar el mensaje específico de la API sin Reintentar y mantener el diálogo abierto.
  - Si la API responde con error de red/timeout/5xx, el sistema deberá mostrar "Error de conexión con el servidor" con Reintentar que reejecute solo la baja.
  - Cuando la API confirme baja exitosa, el sistema deberá cerrar el diálogo, mostrar "Proveedor dado de baja correctamente" (banner 3s) y revalidar el listado; el proveedor dejará de aparecer al no ser devuelto por la API; si el listado revalidado queda vacío (de 1 a 0), mostrar `EmptyState`; la baja debe permitirse aunque existan movimientos previos, y el proveedor inactivo permanecerá consultable por detalle en backend pero no en este listado.

### RF-5 — Manejo uniforme de estados y revalidación
El sistema debe reutilizar los patrones base de `005` y garantizar revalidación sin caché, con semántica de contacto.
- **Criterios de aceptación (EARS):**
  - Mientras cualquier operación (carga de listado, alta, edición, baja) esté en curso, el sistema deberá deshabilitar su botón disparador para evitar envíos duplicados locales por doble clic; este deshabilitado no evita concurrencia distribuida entre pestañas/usuarios, que se resuelve mostrando el 4xx específico de la API.
  - Cuando el encargado informe un contacto opcional que queda vacío tras `trim` (`""` o `"   "`), el sistema deberá bloquearlo localmente como error de forma sin llamar a la API (incluye `null`/ausente vs `""`); el backend valida `""` como violación si se envía, pero el frontend nunca lo envía.
  - Cuando una operación concurrente sobre el mismo `codigo` sea rechazada por la API (ej. alta duplicada simultánea, edición/baja concurrente, edición que envía `null` mientras otro edita mismo campo), el sistema deberá mostrar el mensaje 4xx específico devuelto sin lógica de bloqueo adicional en el frontend.
  - Cuando cualquier operación modifique el catálogo con éxito, el sistema deberá revalidar el listado pidiéndolo de nuevo a la API y no usar `localStorage`/`sessionStorage`; si la revalidación falla con 401/red/5xx, se mostrará el error del listado correspondiente manteniendo el banner de éxito (coexistencia 3s).
  - Si la API responde con 401, el sistema deberá tratarlo como cualquier otro 4xx mostrando el mensaje de la API sin redirección; si la revalidación posterior falla con 401, se mostrará como `ErrorMessage` validacion sin Reintentar además del éxito.

## Requisitos no funcionales
- **RNF-1 — Fuente de verdad API:** el frontend valida solo presencia tras `trim` para `codigo`/`nombre` y que opcional informado no quede vacío (`""`/`"   "`); longitudes, formatos de `email` (`local@domino.tld`), `telefono` (7-15 dígitos, `+` solo al inicio), `direccion` (5-200 imprimibles), unicidad de código y normalización `trim+mayúsculas` (solo extremos, sin colapsar internos, ej. `"AB 123"` conserva espacio interior) los decide el backend y sus mensajes se muestran tal cual sin anticipar.
- **RNF-2 — Reutilización de base 005/006:** listado y formularios usan `Loading` ("Cargando..."), `EmptyState` ("Sin datos disponibles") y `ErrorMessage` con dos niveles (4xx mensaje API sin Reintentar vs red/5xx genérico con Reintentar) sin variantes; mensajes de éxito son banners breves separados (`role="status"` `aria-live="polite"` 3s), mismo patrón que `006`.
- **RNF-3 — Estado solo en memoria:** sin persistencia en cliente; todo dato se revalida contra la API tras mutación (constitución frontend §5).
- **RNF-4 — Mantenibilidad junior:** flujo modal en misma pantalla, sin paginación/búsqueda, sin estado global, con `codigo` excluido del payload de edición y semántica `null` (borrar con acción explícita) / `ausente` (conservar) / `""` (bloqueo local) clara.
- **RNF-5 — Mensajes en español:** navegación, placeholders, errores y éxitos breves en español; los dos genéricos de `005` sin variantes; los mensajes 4xx de `002` ya son en español por `002` RNF-2, por lo que mostrarlos tal cual no viola idioma (si un 4xx viniera en otro idioma, se mostraría tal cual sin traducir, sin exponer stack).
- **RNF-6 — Accesibilidad mínima:** formulario modal con `label` asociado a cada input (`htmlFor`/`id`), foco visible, navegación por teclado, `role="dialog"` para modal/confirmación y `role="alert"` para errores; botón "Borrar" para `null` accesible por teclado; no se exige WCAG completo.

## Casos límite
- Listado vacío legítimo → EmptyState; transición de 1 a 0 tras baja revalidada muestra EmptyState manteniendo banner éxito 3s.
- Listado con error 4xx sin mensaje o cuerpo no JSON → genérico validación "No se pudo completar la solicitud. Revisa los datos e intenta nuevamente." sin Reintentar.
- Alta con código duplicado que difiere solo en mayúsculas/espacios extremos (`"  ab-01 "` vs `"AB-01"`) → backend rechaza por normalización `trim+mayúsculas` sin colapsar internos, frontend muestra mensaje específico.
- Alta con código `__`/`--`/`*`/`ñ`/emoji/espacios internos (`"AB 123"` con espacio interior conservado)/2/21 caracteres, nombre 1/101, email sin `@`/sin punto/255/`""`/`"   "`, teléfono 6/16 dígitos/letras/`+` en medio/`""`, dirección 4/201/`\n`/`""` → backend valida, frontend solo bloquea presencia vacía; `null`/ausente no se valida en frontend y `TEST@EXAMPLE.COM` se acepta y normaliza a minúsculas en backend.
- Alta con email `TEST@EXAMPLE.COM` debe normalizarse a minúsculas en backend y aceptarse; `null`/ausente para contacto debe aceptarse sin validar.
- Edición que envía `{"email":null}` debe borrar email; que omite `email` debe dejarlo igual; que envía `{"email":""}`/`"   "` debe rechazarse localmente sin llamar API; payload vacío `{}` o sin cambios debe rechazarse localmente con "Sin cambios" sin llamar API.
- Edición con modal abierto y proveedor dado de baja por otro usuario entre apertura y envío → backend 4xx `no editable`/`no encontrado`, frontend mantiene modal con mensaje y no revalida como éxito.
- Múltiples clics rápidos en Crear/Guardar/Confirmar → botón deshabilitado mientras cargando, sin duplicados locales.
- Concurrencia alta simultánea mismo código (dos altas, edición con `null` vs edición con valor) → una 201, la otra 409 específico.
- Revalidación del listado falla con red/5xx/401 tras alta/edición/baja exitosa → se mantiene éxito 3s y se muestra además error del listado con Reintentar (si 401, sin Reintentar).
- Cierre de diálogo/navegación mientras petición en curso → petición no se cancela, ESC ignorado, al volver se revalida y se muestra resultado.
- Error de red/timeout/5xx en cualquier operación → "Error de conexión con el servidor" con Reintentar.
- 401 en cualquier operación o revalidación → tratado como 4xx estándar sin redirección, sin Reintentar.

## Fuera de alcance
- Búsqueda/filtros por texto, paginación, ordenamiento y columnas adicionales (ej. estado, fecha creación); el orden por `codigo` lo garantiza la API, el frontend no lo implementa.
- Vista de detalle individual de proveedor (incluidos inactivos de `002` RF-3); la trazabilidad permanece vía `GET /proveedores/{codigo}` en la API pero no se muestra en esta pantalla (el listado nunca muestra `estado`).
- Gestión de movimientos de inventario, validación de stock y referencia obligatoria a proveedor en entradas (`003`); tras la baja, `003` rechazará nuevas entradas con ese proveedor, pero esta pantalla no lo valida.
- Gestión de productos, categorías, stock actual y alertas.
- Reactivación de proveedores inactivos, borrado físico y edición de código o de estado directo.
- Gestión de compras, facturas, precios y pagos.
- Internacionalización, tema oscuro, notificaciones/toasts globales y adaptación responsive dedicada.
- Autenticación/autorización (401 como 4xx estándar).

## Criterios de finalización
- RF-1 a RF-5 verificados según EARS: listado 5 columnas ordenado por código (API) con EmptyState/Loading/ErrorMessage (con "—" para `null`), alta modal 5 campos con validación solo presencia y semántica opcional (`null` borra con acción explícita, ausente conserva, `""`/`"   "` bloquea), edición con código solo lectura y semántica `null`/ausente/`""`/vacío y `""` con `trim` bloqueado, baja con confirmación y desaparición tras revalidación (1→0 muestra EmptyState), estados uniformes y revalidación sin caché.
- Mensajes de error usan dos niveles de `005` (4xx mensaje API sin Reintentar vs red/5xx genérico con Reintentar) y mensajes de éxito breves en español como banners `role="status"` 3s separados, coexistiendo con error de revalidación si ocurre.
- Botones deshabilitados mientras cargando, sin duplicados locales; concurrencia y contacto `null` vs `""` vía 4xx específico de API; `codigo` con normalización `trim+mayúsculas` solo extremos (espacio interior conservado) respetada.
- Sin filtros/paginación/detalle/movimientos/`codigo`/`estado` edit/reactivación incluidos; orden por `codigo` no implementado en frontend.
- Pruebas de componente para listado, alta, edición y baja con `fetch` mockeado según constitución frontend §4: `npm run test` verde y `npm run lint` sin errores.
- `npm run dev` muestra pantalla proveedores contra backend real con las 4 operaciones funcionando, revalidación visible, transición a EmptyState tras última baja y manejo de `null` (borrado) vs `""` (bloqueo).
- Spec aprobada sin [NECESITA ACLARACIÓN] bloqueante.

## Dudas abiertas
- Ninguna bloqueante. No hay puntos marcados como [NECESITA ACLARACIÓN]; la reactivación de proveedores (pregunta de `002`) se evaluará en spec futura si se requiere.
