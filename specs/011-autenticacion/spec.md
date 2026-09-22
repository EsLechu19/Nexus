# Spec 011 — Autenticación Básica

## Contexto y objetivo
La tienda opera hasta ahora con los catálogos de productos (`001`), proveedores (`002`), movimientos de inventario (`003`) y consulta de stock (`004`) sin control de acceso: cualquier cliente HTTP puede crear, editar, consultar y dar de baja recursos. Esto deja el inventario —activo crítico del negocio— expuesto a uso no autorizado y sin trazabilidad de quién opera.

Esta funcionalidad introduce autenticación básica como capa transversal obligatoria, sin roles ni permisos diferenciados por ahora (se resolverán en un spec futuro). Un usuario se identifica con email y contraseña, inicia sesión y recibe un token que debe acompañar cada solicitud a los endpoints existentes, que pasan a requerir autenticación obligatoria. No incluye alta pública de usuarios, recuperación de contraseña, ni gestión de permisos.

El objetivo es garantizar que solo usuarios registrados y autenticados puedan operar el sistema, cerrando el acceso anónimo, manteniendo intacta la lógica de negocio ya validada de `001` a `004` y dejando una base mínima para evolucionar hacia roles.

En este spec, los usuarios se crean exclusivamente por fuera de la API (seed directo en base de datos y comando CLI administrativo); la API solo autentica.

## Impacto en specs existentes
`001-productos-catalogo`, `002-proveedores`, `003-movimientos-inventario` y `004-consulta-stock` quedan **modificados por este spec**: sus endpoints pasan de no requerir autenticación a requerirla obligatoriamente. Esto es un cambio consciente y documentado, no una regresión.

Los contratos de negocio, validaciones, cálculos de `stock_actual` y `alerta`, y el carácter append-only definidos en esos specs permanecen intactos; solo se añade una capa previa de autenticación. Como parte de los criterios de finalización de `011`, se debe actualizar el setup de los tests existentes de esos 4 specs para que incluyan un token JWT válido en cada solicitud y confirmar que vuelven a pasar en verde con la autenticación activa. Sin token, esos mismos tests deben ahora esperar `401`.

## Usuarios
- **Encargado de tienda / Operador** — mismo actor de `001`/`002`/`003`/`004`. Ahora debe autenticarse antes de operar: inicia sesión con email y contraseña y opera con token. Percibe el cambio como un paso previo obligatorio, sin cambios en flujos de productos/proveedores/movimientos/stock una vez autenticado.
- **Administrador bootstrap (actor indirecto, fuera de API)** — crea el primer usuario y usuarios adicionales vía comando CLI/seed para que el login sea posible. No interactúa vía HTTP en este MVP.

## Historias de usuario
- **HU-1:** Como encargado, quiero iniciar sesión con mi email y contraseña para obtener un token y poder operar el sistema.
- **HU-2:** Como encargado, quiero que todas las operaciones de productos, proveedores, movimientos y stock exijan mi token, para que el inventario no sea accesible sin autenticación.
- **HU-3:** Como encargado, quiero recibir un error claro y genérico si mis credenciales son inválidas, sin que el sistema revele si el email existe, para no exponer qué cuentas están registradas.
- **HU-4:** Como encargado, quiero que si mi token falta, es inválido o ha expirado, el sistema rechace la operación con error de no autenticado y me obligue a volver a loguearme, sin necesidad de un logout en el servidor.
- **HU-5:** Como encargado, quiero poder descartar mi token en el cliente para cerrar mi sesión localmente, sin depender de una invalidación en el servidor.

## Requisitos funcionales

### RF-1 — Inicio de sesión con email y contraseña
El sistema debe permitir iniciar sesión a un usuario registrado mediante email y contraseña y devolver un token de acceso.
- **Definiciones:** email tras `trim` y normalización debe cumplir la misma validación de formato sintáctico de `002` (formato `local@dominio.tld` con un `@`, dominio con al menos un `.`, TLD >=2, sin espacios, longitud total <=254); es único global e inmutable para el usuario; contraseña en el login es la contraseña en claro enviada por el cliente (mínimo 8 caracteres en la creación, ver RNF), verificada contra la contraseña hasheada almacenada; token es JWT Bearer con expiración de 8 horas cuyo payload contiene únicamente `email` y `exp`, sin roles.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado solicite `POST /api/v1/auth/login` con email existente y contraseña correcta, el sistema deberá responder con éxito y devolver un token JWT de tipo Bearer con expiración de 8 horas.
  - Si el campo `email` o `password` está ausente en el body de la solicitud, el sistema deberá rechazar con `422` (error de validación estructural) y no devolver token.
  - Para cualquier otro caso —email con formato inválido (sin `@`, sin punto en dominio, con espacios), email que no existe, o contraseña incorrecta— el sistema deberá rechazar con `401` y mensaje genérico `Credenciales inválidas`, sin distinción entre esos casos.
  - El sistema nunca deberá exponer el hash de la contraseña ni la contraseña en claro en ninguna respuesta, bajo ninguna circunstancia.
  - Cuando el login sea exitoso, el token devuelto deberá ser utilizable inmediatamente como `Authorization: Bearer <token>` en los endpoints protegidos.

### RF-2 — Protección obligatoria de endpoints existentes
El sistema debe exigir autenticación Bearer válida para todos los endpoints de negocio ya existentes, sin excepción por método HTTP.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado solicite cualquier `GET`, `POST`, `PATCH` o `DELETE` bajo `/api/v1/productos`, `/api/v1/proveedores`, `/api/v1/movimientos/*` o `/api/v1/stock` y `/api/v1/stock/{codigo}` sin header `Authorization` o con valor que no sea `Bearer <token>`, el sistema deberá rechazar con `401`.
  - El sistema deberá validar el token JWT siempre **antes** de cualquier acceso a base de datos, incluyendo antes de tomar cualquier lock (`SELECT FOR UPDATE`). Un `401` por token faltante, inválido o expirado nunca deberá dejar un lock tomado innecesariamente.
  - Cuando el token sea inválido (firma incorrecta, malformado, con prefijo distinto a `Bearer`) o haya expirado (más de 8 horas desde emisión), el sistema deberá rechazar con `401` y no ejecutar la operación de negocio.
  - Cuando el token sea válido y no expirado, el sistema deberá ejecutar la operación solicitada con la misma lógica, validaciones y respuestas ya definidas en `001`/`002`/`003`/`004`, sin cambios.
  - El sistema deberá aplicar la misma exigencia de token a todos los métodos, incluyendo los `GET` de consulta y listado.

### RF-3 — Endpoints públicos y documentación
El sistema debe mantener públicos solo el login y la visualización de la documentación, manteniendo protegida la ejecución.
- **Criterios de aceptación (EARS):**
  - Cuando cualquier cliente solicite `POST /api/v1/auth/login`, el sistema deberá permitirlo sin token.
  - Cuando cualquier cliente solicite los endpoints de documentación de desarrollo (`GET /docs`, `GET /openapi.json`), que no siguen la convención `/api/v1/*` pero se consideran públicos igualmente para fines de desarrollo, el sistema deberá permitir la visualización sin token.
  - Cuando se intente ejecutar cualquier endpoint protegido desde `Try it out` de `/docs` sin `Authorize` Bearer válido, el sistema deberá responder `401`, de forma idéntica a una llamada directa sin token.
  - Ningún otro endpoint bajo `/api/v1/*` deberá ser accesible sin token.

### RF-4 — Modelo mínimo de usuario y creación fuera de API
El sistema debe persistir usuarios con el modelo mínimo y sin exponer credenciales, creándolos solo por fuera de la API.
- **Criterios de aceptación (EARS):**
  - Cuando el administrador cree un usuario por el medio administrativo previsto (seed o comando CLI administrativo), el sistema deberá persistir únicamente `email` único (validado como en RF-1) y `password` hasheada; ningún otro campo (`nombre`, `rol`, `estado`) deberá ser requerido ni persistido en este MVP.
  - Cuando el administrador ejecute el comando CLI para crear un usuario con email ya existente (tras normalización), el comando deberá rechazar por duplicado y no crear el usuario.
  - Cuando el administrador ejecute el comando CLI con contraseña de menos de 8 caracteres, el comando deberá rechazar con error de validación.
  - El sistema nunca deberá incluir el hash de la contraseña en ninguna respuesta de lectura o escritura de la API, ni siquiera para el propio usuario autenticado.
  - No existirá endpoint HTTP de alta, edición, baja o listado de usuarios en este MVP; cualquier intento de `POST /api/v1/usuarios` u otro similar deberá responder `404` por no existir.

### RF-5 — Cierre de sesión del lado del cliente y expiración
El sistema debe permitir el cierre de sesión solo descartando el token en el cliente, sin invalidación en el servidor, y exigir nuevo login al expirar.
- **Criterios de aceptación (EARS):**
  - Cuando el token expire (8 horas), cualquier solicitud posterior con ese token deberá ser rechazada con `401`, obligando al encargado a volver a solicitar `POST /api/v1/auth/login` para obtener un nuevo token.
  - No existirá endpoint de logout ni de refresh ni de revocación de token en el backend para este MVP; el sistema deberá considerar válido cualquier JWT firmado y no expirado hasta su `exp`.
  - Cuando el encargado descarte el token en memoria del cliente (logout del frontend), el sistema no deberá requerir ninguna llamada al backend; la siguiente solicitud sin token deberá ser rechazada por RF-2 con `401`.

## Requisitos no funcionales
- **RNF-1 — Confidencialidad de credenciales:** la contraseña se almacena solo hasheada, nunca en claro ni reversible; ningún log, traza o respuesta expone hash o contraseña. Verificación: inspección de respuestas y almacenamiento.
- **RNF-2 — Validez temporal del token:** el JWT expira a las 8 horas desde emisión (`exp`), es stateless y no requiere almacenamiento de sesión en el servidor. Verificación: `exp` dentro del payload y `401` tras expiración.
- **RNF-3 — Unicidad y formato de email:** `email` es único global (incluyendo normalización) y con la misma validación sintáctica de `002`; no se valida existencia de dominio. Verificación: pruebas de formato y duplicado.
- **RNF-4 — Mensajes y seguridad por oscuridad:** los errores de login son genéricos `Credenciales inválidas` con `401`, sin distinguir `email no encontrado` vs `contraseña incorrecta`, y todos los errores mantienen mensajes en español sin filtrar datos sensibles. Verificación: pruebas de login fallido.
- **RNF-5 — Ausencia consciente de mitigación de fuerza bruta:** para este MVP no se implementa bloqueo temporal ni rate limiting ni retardo en `POST /auth/login`; ante credenciales inválidas siempre se responde `401` inmediato (salvo el caso de campos ausentes que es `422` según RF-1). Esta es una limitación aceptada y documentada, que deja al sistema expuesto a intentos de fuerza bruta, a resolver en un spec futuro de seguridad si se decide profundizar. Verificación: revisión de RF-1 y casos límite.
- **RNF-6 — Sin regresión funcional:** toda la lógica de `001`/`002`/`003`/`004` (validaciones, cálculo de `stock_actual`, `alerta`, append-only) permanece intacta; solo se añade la capa de autenticación previa. Verificación: suite existente sigue verde con token (ver Impacto en specs existentes).
- **RNF-7 — Idioma:** mensajes visibles y de error siguen en español.
- **RNF-8 — Validez residual de JWT stateless:** al ser JWT stateless sin lista de revocación, un token sigue siendo válido hasta su `exp` natural de 8 horas incluso si el usuario fue eliminado de la base de datos en ese lapso. Esta es una limitación consciente y aceptada de este diseño, no un defecto a corregir en este MVP. Verificación: emisión de token, borrado del usuario fuera de API y uso posterior del token hasta `exp` debe seguir siendo `200` si la firma es válida.

## Casos límite
- Login con email con espacios extremos, mayúsculas o `+` debe normalizarse para búsqueda pero rechazarse si viola formato; si `email` o `password` están ausentes en el body debe ser `422`, en cualquier otro caso de formato inválido debe ser `401 Credenciales inválidas` (regla de dos niveles de RF-1).
- Login con contraseña de 7 caracteres, `""` o `null` debe rechazarse con validación en la creación (CLI) y con `401` genérico en el login si no coincide (salvo campo ausente que es `422`).
- Login con email inexistente vs contraseña errónea para email existente deben responder idéntico `401 Credenciales inválidas` sin pistas.
- Solicitud con header `Authorization` ausente, vacío, con `Bearer` sin token, con `Basic`, con token truncado, con firma alterada o con `exp` pasado 8h debe ser `401` sin ejecutar negocio.
- Token con `email` de usuario que luego fue eliminado (si ocurriera por borrado directo en BD) debe seguir siendo considerado válido hasta `exp` si la firma es válida, dado que no hay revocación en este MVP.
- Usuario creado con email duplicado que difiere solo en mayúsculas/espacios debe rechazarse por unicidad normalizada.
- Acceso a `/api/v1/stock` con token válido pero producto `inactivo` debe seguir respondiendo `404` según `004`, no `401`; la autenticación no cambia la semántica de negocio.
- Intento de enviar contraseña o hash en `GET` o en respuestas de `productos`/`stock` debe ser ignorado/nunca expuesto.

## Fuera de alcance
- Registro público de usuarios (`POST /api/v1/usuarios` o similar) y cualquier endpoint HTTP de gestión de usuarios (alta/edición/baja/listado); la creación es solo seed/CLI fuera de API.
- Recuperación de contraseña, reset, cambio de contraseña por el propio usuario y verificación de email.
- Roles y permisos diferenciados (admin, vendedor, lector); todo usuario autenticado tiene el mismo acceso total a `001`–`004` en este MVP.
- Refresh token, rotación de tokens, logout/invalidación en el servidor y lista de revocación.
- Bloqueo temporal, rate limiting, CAPTCHA, retardo artificial y cualquier mitigación de fuerza bruta.
- Complejidad adicional de contraseña más allá de mínimo 8 caracteres (mayúsculas/números/símbolos) y políticas de expiración forzada.
- Campos adicionales de usuario (`nombre`, `rol`, `estado`, `avatar`) y perfil.
- Autorización a nivel de recurso o auditoría de quién realizó cada movimiento (trazabilidad por usuario).

## Criterios de finalización
- RF-1 a RF-5 implementados y verificados según sus criterios EARS: login con email validado como en `002` retorna JWT Bearer 8h con payload `email+exp` y mensaje genérico `401`; todos los `/api/v1/productos|proveedores|movimientos|stock` requieren Bearer y responden `401` si falta/inválido/expirado sin excepción por método; `/docs` visualizable pero `Try it out` protegido; modelo solo `email+password` hasheada sin exposición; logout solo cliente y expiración exige nuevo login.
- Validaciones de email (formato `002`, unicidad) y contraseña (≥8) cubiertas con pruebas, incluyendo `null`/ausente vs `""` y hash nunca expuesto.
- Sin endpoint HTTP de usuarios; creación solo vía seed/CLI documentada en plan.
- Suite existente de `001`–`004` sigue verde cuando se envía token, y `401` sin token; ningún `UPDATE`/`DELETE` sobre histórico y `stock_actual` intacto.
- `RNF-5` documentado como limitación aceptada de no mitigación de fuerza bruta.
- Spec aprobada sin [NECESITA ACLARACIÓN] bloqueante.

## Dudas abiertas
- Ninguna bloqueante para este MVP. Queda como [NECESITA ACLARACIÓN] para specs futuros si se debe añadir `nombre` o `estado` al usuario, o si la mitigación de fuerza bruta (rate limiting) debe ser por IP o por email.
