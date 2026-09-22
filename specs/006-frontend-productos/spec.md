# Spec 006 — Frontend Productos (Gestión de Catálogo)

## Contexto y objetivo
La tienda necesita gestionar su catálogo de productos (juegos, consolas y accesorios) desde la interfaz web, apoyándose en el esqueleto base ya construido en `005-frontend-base` (layout con navegación, cliente API centralizado y componentes base de cargando/error/vacío). Esta funcionalidad entrega exclusivamente la pantalla de productos que consume el backend definido en `001-productos-catalogo` (alta con SKU/nombre/categoría/stock_inicial, listado de activos, edición de nombre/categoría y baja lógica), sin incluir movimientos de stock ni consulta de stock dinámico. Es prerrequisito para que las pantallas de movimientos y stock puedan referenciar productos existentes.

## Usuarios
- **Encargado de catálogo:** mantiene el catálogo al día (único actor del MVP). Sin autenticación ni roles; es el mismo operador de tienda de `005` enfocado en productos.

## Historias de usuario
- **HU-1:** Como encargado, quiero ver el listado de productos activos con su SKU, nombre, categoría y stock inicial para verificar el catálogo vigente.
- **HU-2:** Como encargado, quiero crear un producto nuevo indicando nombre, SKU, categoría y stock inicial opcional para incorporarlo al catálogo.
- **HU-3:** Como encargado, quiero editar el nombre y la categoría de un producto activo para corregir datos sin cambiar su identidad.
- **HU-4:** Como encargado, quiero dar de baja lógica un producto activo para retirarlo del listado sin borrar su historial.
- **HU-5:** Como encargado, quiero entender qué pasó cuando una operación falla (validación o conexión) para corregir o reintentar sin perder contexto.

## Requisitos funcionales

### RF-1 — Listado de productos activos
El sistema debe mostrar el listado de productos activos obtenido de la API, con cuatro columnas fijas y estados uniformes reutilizados de `005`.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado acceda a la sección productos, el sistema deberá pedir el listado a la API y mostrar cada producto con `sku` (normalizado), `nombre`, `categoria` y `stock_inicial` en una tabla sin filtros, sin ordenamiento y sin paginación; la foto completa es tal cual la devuelve la API, sin ordenar en el frontend, con scroll vertical si crece y sin truncar.
  - Mientras se espera la respuesta de la API, el sistema deberá mostrar el estado cargando uniforme con texto "Cargando...".
  - Cuando la API devuelva lista vacía, el sistema deberá mostrar el estado vacío con mensaje "Sin datos disponibles".
  - Cuando la API responda con error 4xx, el sistema deberá mostrar el mensaje específico devuelto por la API sin botón Reintentar; cuando sea error de red, timeout o 5xx, deberá mostrar "Error de conexión con el servidor" con botón "Reintentar" que reejecute solo la carga del listado sin perder la sección.
  - El sistema no deberá mostrar columna de estado, ya que el listado solo contiene activos por contrato de `001`; el orden mostrado es el que entrega la API sin garantía adicional.

### RF-2 — Alta de producto
El sistema debe permitir crear un producto mediante formulario modal dentro de la pantalla de listado.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado accione "Crear producto", el sistema deberá abrir un formulario modal con campos `nombre` (texto), `SKU` (texto), `categoria` (selector con opciones `videojuego` | `consola` | `accesorio`) y `stock_inicial` (input numérico opcional, permite vacío; por defecto vacío que se envía como ausencia para que el backend lo trate como 0 según `001` RF-1).
  - Si algún campo requerido está vacío tras `trim` (SKU/nombre/categoría), el sistema deberá señalar el error de forma en el formulario sin llamar a la API; el frontend valida solo presencia tras trim, no valida duplicidad de SKU, longitud 3-20, patrón alfanumérico/-/_ , rango de stock ni enum más allá de requerido — esas reglas las decide el backend.
  - Cuando el encargado envíe el formulario con forma válida, el sistema deberá enviar la creación a la API y deshabilitar el botón de envío mientras la petición está en curso para evitar duplicados por doble clic (no evita concurrencia distribuida).
  - Si la API responde con error 4xx (ej. SKU duplicado normalizado, longitud/formato inválido, enum no permitido, stock fuera de rango), el sistema deberá mantener el modal abierto y mostrar el mensaje específico devuelto por la API sin reintento automático.
  - Si la API responde con error de red, timeout o 5xx, el sistema deberá mantener el modal abierto y mostrar "Error de conexión con el servidor" con opción Reintentar que reejecute solo el alta.
  - Cuando la API confirme alta exitosa, el sistema deberá cerrar el modal, mostrar mensaje breve "Producto creado correctamente" como banner dentro de la pantalla (visible 3 segundos, distinto de `ErrorMessage`), y revalidar el listado pidiéndolo de nuevo a la API (sin persistencia en cliente); si la revalidación posterior falla con error de red/5xx, el sistema deberá mostrar el error de listado correspondiente manteniendo el mensaje de éxito ya mostrado.

### RF-3 — Edición de producto activo
El sistema debe permitir editar nombre y categoría de un producto activo reutilizando el mismo formulario modal.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado accione "Editar" en la fila de un producto activo, el sistema deberá abrir el modal con `SKU` visible pero deshabilitado (solo lectura, no se envía en el payload), y `nombre` y `categoria` precargados con los valores actuales; `stock_inicial` no se mostrará editable.
  - Si el producto está inactivo, el sistema no lo mostrará en el listado (por `001` RF-2); el criterio de botón Editar deshabilitado/oculto para inactivos es defensivo para carrera (ej. otro usuario lo dio de baja entre carga y clic) — en flujo normal no se alcanza.
  - Si el encargado envía cambios con forma inválida (ej. nombre vacío tras trim, categoría no seleccionada), el sistema deberá señalar el error de forma sin llamar a la API.
  - Cuando el encargado envíe cambios válidos, el sistema deberá enviar a la API solo `nombre` y `categoria` (sin incluir `sku`, `stock` ni `estado`) y deshabilitar el botón mientras la petición está en curso.
  - Si la API responde con error 4xx (ej. nombre inválido, categoría no permitida, producto ya inactivo o no encontrado por concurrencia, SKU inmutable distinto si se enviara), el sistema deberá mantener el modal abierto y mostrar el mensaje específico de la API sin reintento.
  - Si la API responde con error de red/timeout/5xx, el sistema deberá mantener el modal abierto y mostrar "Error de conexión con el servidor" con Reintentar.
  - Cuando la API confirme edición exitosa, el sistema deberá cerrar el modal, mostrar "Producto actualizado correctamente" y revalidar el listado contra la API; si la revalidación falla, mostrar error de listado sin perder el éxito.

### RF-4 — Baja lógica de producto
El sistema debe permitir dar de baja lógica un producto activo con confirmación explícita.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado accione "Dar de baja" en la fila de un producto activo, el sistema deberá abrir un diálogo de confirmación con texto "¿Dar de baja a <nombre> (<SKU>)? No se puede deshacer desde este MVP" y opciones Confirmar/Cancelar.
  - Si el encargado cancela o cierra el diálogo con ESC/navegación mientras no hay petición en curso, el sistema deberá cerrar el diálogo sin efecto.
  - Si el encargado confirma, el sistema deberá enviar la baja a la API y deshabilitar el botón Confirmar mientras la petición está en curso; si el usuario intenta cerrar el diálogo o navegar durante la petición, la petición deberá mantenerse en curso y no cancelarse.
  - Si la API responde con error 4xx (ej. SKU no encontrado o ya dado de baja por concurrencia), el sistema deberá mostrar el mensaje específico de la API sin Reintentar y mantener el diálogo abierto o cerrarlo según el error, permitiendo reintento manual solo para red/5xx.
  - Si la API responde con error de red/timeout/5xx, el sistema deberá mostrar "Error de conexión con el servidor" con Reintentar que reejecute solo la baja.
  - Cuando la API confirme baja exitosa, el sistema deberá cerrar el diálogo, mostrar "Producto dado de baja correctamente" y revalidar el listado; el producto dejará de aparecer al no ser devuelto por la API; si el listado revalidado queda vacío (de 1 a 0), mostrar `EmptyState`.

### RF-5 — Manejo uniforme de estados y revalidación
El sistema debe reutilizar los patrones base de `005` y garantizar revalidación sin caché.
- **Criterios de aceptación (EARS):**
  - Mientras cualquier operación (carga de listado, alta, edición, baja) esté en curso, el sistema deberá deshabilitar su botón disparador para evitar envíos duplicados locales por doble clic; este deshabilitado no evita concurrencia distribuida entre pestañas/usuarios, que se resuelve mostrando el 4xx específico de la API.
  - Cuando una operación concurrente sobre el mismo SKU sea rechazada por la API (ej. alta duplicada simultánea, edición/baja concurrente, edición sobre producto que se volvió inactivo entre apertura de modal y envío), el sistema deberá mostrar el mensaje 4xx específico devuelto sin lógica de bloqueo adicional en el frontend.
  - Cuando cualquier operación modifique el catálogo con éxito, el sistema deberá revalidar el listado pidiéndolo de nuevo a la API y no usar `localStorage`/`sessionStorage` para inventario; si la revalidación falla, mostrar el estado de error del listado correspondiente.
  - Si la API responde con 401, el sistema deberá tratarlo como cualquier otro 4xx mostrando el mensaje de la API sin redirección, en español tal cual lo entrega el backend (que por `001` RNF-2 ya es en español, por lo que no hay conflicto con `frontend` constitución §6).

## Requisitos no funcionales
- **RNF-1 — Fuente de verdad API:** el frontend valida solo presencia tras trim (requerido) para `nombre`/`SKU`/`categoria` y que `stock_inicial` sea entero si se informa; duplicidad de SKU, longitud 3-20, patrón `^[A-Z0-9_-]+$`, enum exacto tras `trim+minúsculas`, y rango `0..1_000_000` los decide el backend y sus mensajes se muestran tal cual sin anticipar.
- **RNF-2 — Reutilización de base 005:** listado y formularios usan `Loading` ("Cargando..."), `EmptyState` ("Sin datos disponibles") y `ErrorMessage` con dos niveles (4xx mensaje API sin Reintentar vs red/5xx genérico con Reintentar) sin variantes; mensajes de éxito son banners breves separados, visibles 3 segundos.
- **RNF-3 — Estado solo en memoria:** sin persistencia en cliente; todo dato se revalida contra la API tras mutación (constitución frontend §5); `stock_inicial` vacío se envía como ausencia/`undefined` para que el backend lo trate como 0 y no genere traza, respetando `001` RNF-1 append-only.
- **RNF-4 — Mantenibilidad junior:** flujo modal en misma pantalla, sin paginación/búsqueda, sin estado global, con `sku` excluido del payload de edición.
- **RNF-5 — Mensajes en español:** navegación, placeholders, errores y éxitos breves en español; los dos genéricos de `005` sin variantes; los mensajes 4xx de `001` ya son en español por `001` RNF-2, por lo que mostrarlos tal cual no viola idioma.
- **RNF-6 — Accesibilidad mínima:** formulario modal con `label` asociado a cada input (`htmlFor`/`id`), foco visible, navegación por teclado, `role="dialog"` para modal/confirmación y `role="alert"` para errores; no se exige WCAG completo.

## Casos límite
- Listado vacío legítimo → EmptyState diferenciado de cargando/error; transición de 1 a 0 tras baja revalidada muestra EmptyState.
- Listado con error 4xx sin mensaje o cuerpo no JSON → genérico validación "No se pudo completar la solicitud. Revisa los datos e intenta nuevamente." sin Reintentar.
- Alta con SKU duplicado que difiere solo en mayúsculas/espacios → backend rechaza por normalización `trim+mayúsculas`, frontend muestra mensaje específico.
- Alta con SKU con espacios interiores (`"AB 123"`), `*`, `ñ`, longitud 2/21, nombre 1/101, categoría `Videojuego`/`juego`/`CONSOLA`/` consola `, stock `""` (vacío→ausencia→0), `" 0 "` , `"001"`, `"1.0"`, `"-1"`, `"abc"`, `>1_000_000` → backend valida, frontend solo bloquea vacío y deja que la API informe; `stock_inicial` vacío no se envía como `"0"` sino como ausencia.
- Edición con modal abierto y producto dado de baja por otro usuario entre apertura y envío → backend responde 4xx `no editable`/`no encontrado`, frontend muestra mensaje y mantiene modal.
- Edición con payload vacío o con campos extra `sku` distinto/`stock`/`estado` → frontend solo envía `nombre`/`categoria`, backend ignora extras o rechaza `sku` distinto según `001`.
- Múltiples clics rápidos en Crear/Guardar/Confirmar → botón deshabilitado mientras cargando, sin peticiones duplicadas locales.
- Concurrencia alta simultánea mismo SKU (dos altas, edición+baja) → una tiene éxito, la otra recibe 4xx específico que se muestra.
- Revalidación del listado falla con red/5xx tras alta/edición/baja exitosa → se mantiene mensaje de éxito y se muestra además el error del listado con Reintentar.
- Cierre de diálogo/navegación mientras petición de baja/edición está en curso → petición no se cancela, al volver se debe revalidar.
- Error de red/timeout/5xx en cualquier operación → "Error de conexión con el servidor" con Reintentar que reejecuta solo esa operación sin perder listado/modal.
- 401 en cualquier operación → tratado como 4xx estándar sin redirección.

## Fuera de alcance
- Búsqueda/filtros por texto, paginación, ordenamiento y columnas adicionales (ej. estado, fecha creación).
- Vista de detalle individual de producto (incluidos inactivos de `001` RF-3); la trazabilidad de inactivos permanece disponible vía API pero no se muestra en esta pantalla.
- Consulta de stock actual dinámico, historial y trazabilidad de movimientos (specs `008`/`009`).
- Edición directa de `SKU` o `stock_inicial`/`stock` y reactivación de productos inactivos.
- Borrado físico, importación masiva y gestión de proveedores.
- Internacionalización, tema oscuro, notificaciones/toasts globales y adaptación responsive dedicada.
- Autenticación/autorización (401 como 4xx estándar).

## Criterios de finalización
- RF-1 a RF-5 verificados según EARS: listado 4 columnas sin ordenar/paginar con EmptyState/Loading/ErrorMessage, alta modal 4 campos con validación solo presencia y mensajes 4xx de API, edición con SKU solo lectura (payload sin SKU) e inactivos defensivos, baja con confirmación y desaparición tras revalidación (1→0 muestra EmptyState), estados uniformes y revalidación sin caché (vacío enviado como ausencia).
- Mensajes de error usan dos niveles de `005` (4xx mensaje API sin Reintentar vs red/5xx genérico con Reintentar) y mensajes de éxito breves en español como banners de 3s separados.
- Botones deshabilitados mientras cargando, sin duplicados locales; concurrencia distribuida resuelta mostrando 4xx específico de API.
- Sin filtros/paginación/detalle/stock dinámico/SKU-stock edit/reactivación incluidos.
- Pruebas de componente para listado, alta, edición y baja con `fetch` mockeado según constitución frontend §4: `npm run test` verde y `npm run lint` sin errores.
- `npm run dev` muestra pantalla productos contra backend real con las 4 operaciones funcionando, revalidación visible y transición a EmptyState tras última baja.
- Spec aprobada sin [NECESITA ACLARACIÓN] bloqueante.

## Dudas abiertas
- Ninguna bloqueante. No hay puntos marcados como [NECESITA ACLARACIÓN]; paginación/búsqueda, detalle de inactivos y stock dinámico se evaluarán en specs futuras si se requieren.
