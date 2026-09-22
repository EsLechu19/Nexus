# Spec 013 — Pantalla de Autenticación Frontend

## Contexto y objetivo

La tienda dispone de una interfaz web con cuatro pantallas de gestión de inventario (productos, proveedores, movimientos y stock) construidas sobre el esqueleto de `005-frontend-base`, y de una futura pantalla de ventas. Hasta ahora, todas esas pantallas eran accesibles sin control de acceso, coherente con que el backend tampoco exigía autenticación antes de `011`.

Con `011-autenticacion` el backend pasó a exigir `Authorization: Bearer <JWT>` (8h, payload `email+exp`, mensaje genérico `401 Credenciales inválidas`, `422` solo si faltan campos) en todos los endpoints de negocio `/api/v1/productos|proveedores|movimientos|stock` y futuro `/ventas`, dejando solo `POST /api/v1/auth/login` y la documentación como públicos.

Esta funcionalidad introduce la pantalla de autenticación como puerta de entrada del frontend: el usuario debe completar login con email y contraseña antes de poder acceder a cualquiera de las 4 pantallas existentes y a la futura de ventas. Al autenticarse correctamente, el sistema guarda el JWT exclusivamente en memoria (nunca en persistencia de cliente, por constitución del frontend) y lo adjunta como `Bearer` en cada llamada realizada a través del cliente API centralizado definido en `005`. Todas las rutas existentes pasan a estar protegidas: sin token válido se redirige a login. No modifica la lógica de negocio de las pantallas existentes, solo añade la capa previa de acceso.

## Impacto en specs existentes
`005-frontend-base` queda **modificado por este spec**: su regla RF-5 de tratar `401` como `4xx` genérico sin redirección se **reemplaza** por el nuevo comportamiento de deslogueo global definido aquí. Ese reemplazo es consciente y documentado: la premisa bajo la cual `005` definió `401` como `4xx` (“la API no tiene autenticación”) dejó de ser cierta desde `011-autenticacion` y esta pantalla. El resto de `005` (layout, placeholders, cliente API centralizado, estados `Cargando...`/`Error de conexión con el servidor`/`Sin datos disponibles`, error global de configuración) permanece intacto.

## Usuarios

- **Operador de tienda (encargado/vendedor)** — mismo actor de `005` y `006-009`. Ahora debe autenticarse para operar. Percibe el login como paso previo obligatorio; una vez dentro, navega las 4 pantallas y la futura de ventas sin cambios en sus flujos.
- **Administrador bootstrap (actor indirecto, fuera de UI)** — crea usuarios por seed/CLI para que el login sea posible. No interactúa con esta pantalla; su existencia explica por qué no hay registro en la UI.

## Historias de usuario

- **HU-1:** Como operador, quiero iniciar sesión con mi email y contraseña en una pantalla dedicada para obtener acceso a la gestión de inventario.
- **HU-2:** Como operador, quiero que si intento acceder a cualquier pantalla protegida sin estar autenticado sea redirigido a login y, tras loguearme, vuelva a la pantalla que intentaba visitar, para no perder el contexto de mi deep link.
- **HU-3:** Como operador, quiero que mi sesión se mantenga mientras navego entre productos, proveedores, movimientos, stock y ventas sin tener que volver a loguearme en cada cambio de sección.
- **HU-4:** Como operador, quiero poder cerrar mi sesión de forma visible y rápida desde cualquier pantalla para dejar el mostrador seguro cuando otra persona va a usar el equipo.
- **HU-5:** Como operador, quiero recibir mensajes claros y en español si mis credenciales son incorrectas, si dejé campos vacíos o si hay un problema de conexión, sin que el sistema revele si el email existe.
- **HU-6:** Como operador, quiero que si mi sesión expira mientras estoy trabajando, el sistema me lleve a login con un aviso de expiración para que pueda volver a autenticarme sin perder la intención de la acción que hacía.

## Requisitos funcionales

### RF-1 — Pantalla de login con formulario email y contraseña y validación mínima de forma
El sistema debe ofrecer una pantalla de login dedicada con campos email y contraseña, validación local solo por presencia y manejo de estados de envío, delegando el resto de la validación al backend.

- **Criterios de aceptación (EARS):**
  - Cuando el operador acceda a la pantalla de login, el sistema deberá mostrar un formulario con campos `email` (con `autocomplete="email"`) y `contraseña` (con `autocomplete="current-password"`) y un botón `Iniciar sesión`; el autocompletado del navegador no se bloquea.
  - Si el operador intenta enviar el formulario con `email` vacío o `contraseña` vacía (considerando solo espacios como vacío), el sistema deberá bloquear el envío, no llamar al backend y mostrar el mensaje en español `Campo requerido` asociado a cada campo faltante, sin distinguir otro caso.
  - Cuando el campo `email` contenga cualquier valor no vacío, el sistema deberá permitir el envío sin validar su formato en el frontend; antes de enviar aplicará `trim` al valor de email y cualquier formato inválido será evaluado por el backend.
  - Mientras la petición de login esté en curso, el sistema deberá deshabilitar tanto el botón `Iniciar sesión` como los inputs de `email` y `contraseña` y mostrar un indicador de carga, ignorando clics adicionales hasta recibir respuesta para evitar envíos duplicados.
  - El sistema nunca deberá ofrecer en esta pantalla enlaces o botones hacia registro, recuperación de contraseña o gestión de roles.

### RF-2 — Autenticación contra el backend y guardado del token solo en memoria
El sistema debe autenticar las credenciales contra `POST /api/v1/auth/login` del backend `011` y, solo si la respuesta es exitosa, guardar el JWT en memoria volátil y considerar la sesión iniciada.

- **Criterios de aceptación (EARS):**
  - Cuando el operador envíe `email` y `contraseña` no vacíos, el sistema deberá llamar a `POST /api/v1/auth/login` enviando el `email` tras aplicar `trim` y la `contraseña` tal cual, sin adjuntar nunca el header `Authorization` incluso si hubiera un token previo en memoria.
  - Si el backend responde con éxito y devuelve un token Bearer, el sistema deberá guardar ese token exclusivamente en memoria durante la sesión (nunca en persistencia de cliente) y considerar al operador como autenticado.
  - Si el backend responde `401` a `POST /api/v1/auth/login`, el sistema deberá no guardar ningún token, permanecer en la pantalla de login y mostrar el mensaje en español tal cual lo devuelve el backend: `Credenciales inválidas`, sin diferenciar si el fallo fue por formato, email inexistente o contraseña incorrecta; este `401` de login nunca dispara la regla global de limpieza/redirección de RF-5.
  - Si el backend responde `422` (caso residual, ya que campos vacíos se bloquean localmente), el sistema deberá mostrar el mensaje específico devuelto por el backend en español sin inventar un genérico propio; si el detalle es estructurado (array de errores de Pydantic), mostrará el primer mensaje de forma legible, si es un string simple lo mostrará tal cual.
  - Cuando el backend no responda, responda con error de red o supere el timeout de 10 segundos heredado de `005`, el sistema deberá no guardar token, permanecer en login y mostrar el mensaje genérico en español `Error de conexión con el servidor` con un botón `Reintentar` que reejecuta solo el envío del login, deshabilitado mientras carga.

### RF-3 — Protección de rutas y redirección con memoria de ruta intentada
El sistema debe proteger todas las rutas de negocio existentes y futuras, redirigiendo a login cuando no hay token válido y restaurando la intención de navegación tras autenticación exitosa.

- **Criterios de aceptación (EARS):**
  - Cuando el operador sin token válido solicite cualquier ruta protegida (`/productos`, `/proveedores`, `/movimientos`, `/stock` y futura `/ventas`), el sistema deberá redirigirlo inmediatamente a `/login` sin intentar cargar datos de esa sección ni mostrar su placeholder, y deberá recordar internamente la ruta intentada.
  - Cuando el operador complete un login exitoso habiendo sido redirigido desde una ruta protegida, el sistema deberá redirigirlo automáticamente a esa ruta originalmente intentada (ej. `/stock`).
  - Si el operador accede directamente a `/login` sin haber intentado antes una ruta protegida, el sistema deberá redirigirlo al completar login a la pantalla por defecto `Productos`, que es la primera pestaña de la navegación de `005`.
  - Si el operador ya autenticado intenta acceder a `/login` manualmente, el sistema deberá redirigirlo a la pantalla por defecto `Productos` sin mostrar el formulario de login, ya que no tiene sentido volver a autenticarse; para cambiar de cuenta estando ya logueado el sistema exigirá cerrar sesión explícitamente primero, sin atajo directo.
  - Cuando cualquier recarga de página (`F5`) o cierre/reapertura de pestaña ocurra, el sistema deberá considerar la sesión como cerrada al haberse perdido el token en memoria, mostrar `/login` y, tras un nuevo login, volver a aplicar la regla de redirección a la ruta intentada.

### RF-4 — Cliente API centralizado con inyección de Bearer
El sistema debe canalizar toda comunicación HTTP posterior al login a través del cliente API centralizado definido en `005`, adjuntando automáticamente el token en memoria como `Authorization: Bearer <token>`.

- **Criterios de aceptación (EARS):**
  - Cuando el operador autenticado navegue a cualquier pantalla protegida y esta necesite datos del backend, el sistema deberá realizar la petición usando exclusivamente el cliente API centralizado, incluyendo el header `Authorization: Bearer <token>` cuando exista un token en memoria; toda lógica de inyección y de interceptación de `401` vive dentro de ese cliente centralizado, nunca en componentes de layout o página.
  - Si el operador no está autenticado, el sistema no deberá intentar peticiones de negocio a `/api/v1/*` desde las pantallas protegidas, ya que la redirección de RF-3 debe ocurrir antes.
  - El sistema no deberá persistir el token ni adjuntarlo desde ningún otro punto fuera del cliente centralizado, y `POST /api/v1/auth/login` nunca deberá adjuntar el header `Authorization` incluso si hubiera un token previo en memoria.
  - Cuando el token en memoria sea limpiado por expiración o cierre de sesión, las siguientes llamadas del cliente centralizado deberán dejar de incluir el header `Bearer`.

### RF-5 — Manejo de expiración/sesión inválida y cierre de sesión explícito
El sistema debe tratar el `401` recibido en cualquier pantalla autenticada como señal de sesión inválida/expirada, limpiando la sesión y redirigiendo a login, y debe ofrecer un cierre de sesión manual siempre visible.

- **Criterios de aceptación (EARS):**
  - Cuando cualquier petición realizada vía el cliente centralizado en una sesión autenticada (es decir, con `Bearer` adjunto) reciba `401` del backend (firma inválida, token malformado, expirado tras 8h o sin `Bearer`), el sistema deberá limpiar inmediatamente el token en memoria y redirigir a `/login`, mostrando el mensaje en español `Sesión expirada, inicia sesión nuevamente` que persiste visible en la pantalla de login hasta que el usuario interactúe con el formulario; esta regla nunca aplica a la respuesta de `POST /api/v1/auth/login`, cuyo `401` se trata según RF-2, ni a peticiones que el guard de RF-3 ya bloqueó por falta de token.
  - Mientras exista esa redirección por `401`, el sistema no deberá mostrar simultáneamente un estado de error por sección como los definidos en `005` RF-5; la redirección global prevalece sobre el error local.
  - Para todo otro código de error (`422`/`4xx` distinto de `401`, `5xx`, red/timeout), el sistema deberá mantener el manejo ya definido en `005` RF-5 (mensaje específico del backend si es `4xx` en español, genérico `Error de conexión con el servidor` si es red/`5xx`/timeout) sin limpiar la sesión ni redirigir a login.
  - Cuando el operador accione el botón `Cerrar sesión`, el sistema deberá limpiar el token en memoria de inmediato, sin pedir confirmación y sin llamar al backend (no existe endpoint de logout), redirigir a `/login` y mostrar el mensaje breve `Sesión cerrada correctamente` de forma efímera (3 segundos, mismo patrón ya usado en `006-009`) con el patrón de feedback ya usado en las pantallas existentes.
  - El sistema deberá mostrar el botón `Cerrar sesión` siempre visible en el header del layout solo cuando hay sesión activa, en todas las pantallas protegidas mientras la sesión esté activa, sin esconderlo en un menú; la pantalla de login nunca lo muestra.

## Requisitos no funcionales

- **RNF-1 — Seguridad por no persistencia:** el JWT vive solo en memoria de la pestaña; nunca en `localStorage`, `sessionStorage`, cookies persistentes ni URL. El principio de “sin persistencia en cliente” de la constitución del frontend aplica también al token de sesión, no solo a datos de inventario. Verificación: inspección de cliente API y prueba de recarga → sesión perdida.
- **RNF-2 — Consistencia con `005`:** estados de carga (`Cargando...` deshabilitando botón e inputs), error (`Error de conexión con el servidor` con `Reintentar` solo para red/`5xx`/timeout) y vacío mantienen los mismos textos y patrón visual ya usado; solo el `401` cambia de `4xx` genérico a deslogueo global. Verificación: revisión manual vs `005` RF-5.
- **RNF-3 — Mensajes en español:** toda comunicación visible de esta pantalla (etiquetas, `Campo requerido`, `Credenciales inválidas`, `Sesión expirada, inicia sesión nuevamente`, `Sesión cerrada correctamente`, `Error de conexión con el servidor`) en español. Verificación: revisión manual.
- **RNF-4 — Volatilidad consciente y sesión por pestaña:** la pérdida de sesión tras `F5`/cierre de pestaña es una limitación aceptada, no un defecto; idéntico a la ya aceptada para inventario en `005` RNF-6 y a la ausencia de rate limiting en `011`. Cada pestaña tiene su propia sesión independiente en memoria; abrir una segunda pestaña requiere nuevo login. Verificación: prueba de recarga y prueba con dos pestañas.
- **RNF-5 — Accesibilidad mínima del formulario:** labels asociados a inputs, foco visible, orden de tabulación lógico y botón operable por teclado, coherente con `005` RNF-4. Los inputs llevan `autocomplete="email"` y `autocomplete="current-password"` respectivamente. Verificación: navegación por teclado.

## Casos límite

- Acceso directo sin token a `/stock`, `/movimientos`, `/proveedores`, `/productos` o futura `/ventas` vía URL/bookmark → redirección inmediata a `/login` recordando esa ruta; tras login vuelve a ella sin pasar por `Productos`.
- Acceso directo a `/login` sin token → muestra formulario; acceso a `/login` ya autenticado → redirección a `Productos`.
- Envío con `email` vacío y/o `contraseña` vacía (incluyendo solo espacios) → bloqueo local con `Campo requerido`, sin llamada a `POST /login`.
- Envío con `email` con formato inválido, con espacios extremos o mayúsculas → se envía al backend y backend responde `401 Credenciales inválidas` → se muestra ese mensaje genérico sin revelar si el email existe.
- Backend responde `401 Credenciales inválidas` con cualquier combinación de email inexistente o contraseña incorrecta → mismo mensaje genérico, permanencia en login, sin token.
- Backend responde `422` (residual) → se muestra el mensaje específico del backend tal cual, sin token.
- Backend no responde, error de red, CORS o timeout >10s durante login → `Error de conexión con el servidor` con botón `Reintentar` deshabilitado mientras carga; clics rápidos adicionales ignorados.
- Petición en pantalla protegida devuelve `401` por token expirado/inválido (ej. tras 8h) → limpia token, redirige a `/login` con `Sesión expirada, inicia sesión nuevamente`, sin mostrar error de sección `005`.
- Petición en pantalla protegida devuelve `4xx` distinto de `401` (ej. validación de negocio) o `5xx`/red → se mantiene el manejo por sección de `005` sin desloguear.
- Clic en `Cerrar sesión` en cualquier pantalla protegida → limpia token y redirige a `/login` con `Sesión cerrada correctamente`, sin confirmación y sin llamada a API; siguiente intento a ruta protegida exige nuevo login.
- `F5` estando en `/stock` con sesión activa → token perdido, redirección a `/login` recordando `/stock`; tras nuevo login vuelve a `/stock`.
- Múltiples clics rápidos en `Iniciar sesión` o `Cerrar sesión` → solo el primer clic es procesado, los siguientes se ignoran mientras la acción está en curso.
- Ruta inexistente (`/ruta-inexistente`) sin token → el guard de autenticación se evalúa primero y redirige a `/login` sin llegar a evaluar si la ruta existe, por encima del `404` de `005` RF-2; con token válido, se muestra el `404` normal de `005` sin pasar por login.

## Fuera de alcance

- Registro de nuevos usuarios, alta pública o gestión de usuarios desde la UI (la creación es solo seed/CLI fuera de API según `011` RF-4).
- Recuperación de contraseña, reset, cambio de contraseña por el propio usuario y verificación de email.
- Roles, permisos diferenciados y autorización a nivel de recurso (todo autenticado tiene acceso total, como en `011`).
- Refresh token, rotación, expiración deslizante, logout con invalidación en servidor y lista de revocación.
- Persistencia de sesión (`localStorage`/`sessionStorage`/cookies), modo “recordarme” y restauración tras recarga.
- Mitigación de fuerza bruta (rate limiting, bloqueo, CAPTCHA, retardo) — limitación ya aceptada en `011` RNF-5.
- Internacionalización, tema oscuro, branding definitivo y notificaciones globales (fuera de `005`).
- Adaptación responsive dedicada para móvil/tablet más allá del desktop-first de `005` RNF-5.

## Criterios de finalización

- RF-1 a RF-5 verificados según criterios EARS: pantalla `/login` con formulario email+contraseña, validación local solo `Campo requerido`, botón deshabilitado con carga, sin registro/recuperación/roles.
- Login contra `POST /api/v1/auth/login` guarda JWT solo en memoria y funciona inmediatamente como `Bearer` en el cliente centralizado; `401` genérico y `422` específico mostrados tal cual, red/timeout con `Error de conexión con el servidor` y `Reintentar`.
- RF-3 protegido: sin token, cualquier `/productos|proveedores|movimientos|stock|ventas` redirige a `/login` recordando la ruta; tras login vuelve a la ruta intentada o a `Productos` si no había ruta intentada; `/login` autenticado redirige a `Productos`; `F5` pierde sesión y respeta la regla de retorno.
- RF-4 verificado: ningún componente fuera del cliente centralizado hace `fetch`/adjunta `Bearer`; cliente adjunta `Bearer` solo si hay token en memoria.
- RF-5 verificado: `401` en cualquier pantalla autenticada limpia token y redirige a `/login` con `Sesión expirada, inicia sesión nuevamente` prevaleciendo sobre error de sección; `Cerrar sesión` siempre visible en header, sin confirmación, sin llamada a API, con `Sesión cerrada correctamente` y sin `401` residual.
- `GET /ventas` sin `Bearer` sigue dando `401` a nivel API, ahora provocado por la protección de ruta previa.
- Mensajes en español, volatilidad tras recarga y textos genéricos idénticos a `005` verificados manualmente.
- Pruebas de componente para login (render de formulario, `Campo requerido`, botón deshabilitado durante carga, `401`/`422`/red con `fetch` mockeado según constitución frontend §4): `npm run test` verde y `npm run lint` sin errores.
- Spec aprobada sin `[NECESITA ACLARACIÓN]` bloqueante.

## Dudas abiertas

- [NECESITA ACLARACIÓN] Si en el futuro se introduce `POST /api/v1/auth/refresh` o rotación, ¿debe el cliente centralizado intentar refrescar silenciosamente el token ante un `401` en lugar de redirigir inmediatamente a login?
- [NECESITA ACLARACIÓN] Si se añade rol `admin` vs `vendedor` en un spec futuro, ¿debe la pantalla de login mostrar el rol en el header y ocultar secciones no permitidas, o mantener navegación completa con bloqueo solo a nivel de API?
