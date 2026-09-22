# Spec 005 — Base / Esqueleto Frontend

## Contexto y objetivo
La tienda necesita una interfaz web para gestionar inventario (productos, proveedores, movimientos y stock) que consuma la API REST del backend. Esta funcionalidad crea exclusivamente el esqueleto base de la aplicación frontend: layout general con navegación entre las cuatro secciones, configuración centralizada del cliente de API y componentes base para estados de carga y error. Es prerrequisito de 006-frontend-productos, 007-frontend-proveedores, 008-frontend-movimientos y 009-frontend-stock, y no entrega aún funcionalidad de negocio.

## Usuarios
- **Operador de tienda:** navega entre secciones para gestionar inventario. Único actor del MVP; sin autenticación ni roles.
- **Desarrollador frontend (usuario indirecto):** reutiliza layout, cliente API y estados base para construir 006-009.

## Historias de usuario
- **HU-1:** Como operador, quiero ver una navegación siempre visible con las secciones productos, proveedores, movimientos y stock para moverme sin perder contexto.
- **HU-2:** Como operador, quiero que las secciones aún no implementadas muestren un placeholder claro para entender que están en construcción sin que parezca un error.
- **HU-3:** Como operador, quiero que si accedo a una ruta inexistente se me informe con una página de no encontrado sin romper la navegación.
- **HU-4:** Como operador, quiero que la aplicación se comunique con la API configurada por el entorno para que el mismo esqueleto funcione en local y producción.
- **HU-5:** Como operador, quiero ver estados uniformes de cargando, error con opción de reintentar y vacío para entender qué pasa cuando hay demora o fallo de red.
- **HU-6:** Como operador, quiero que los errores de validación de la API me muestren su mensaje específico y los fallos de servidor/conexión un mensaje genérico comprensible.

## Requisitos funcionales

### RF-1 — Layout general y navegación persistente
El sistema debe ofrecer un layout base con navegación persistente a las cuatro secciones y marcación de sección activa.
- **Criterios de aceptación (EARS):**
  - El sistema debe mostrar en todo momento la navegación con enlaces a productos, proveedores, movimientos y stock.
  - Cuando el operador navegue a una sección, el sistema deberá marcar visualmente esa sección como activa mediante indicador visual y atributo semántico de sección actual.
  - Mientras el operador navegue entre secciones, el sistema deberá mantener la navegación visible sin recargar el layout base y sin perder la ruta, parámetros de URL ni posición de scroll de la navegación.
  - El sistema debe permitir que la navegación sea operable por teclado (foco visible, activación con Enter/Espacio) y sea anunciada correctamente por lector de pantalla como navegación principal.

### RF-2 — Placeholders de secciones y ruta no encontrada
El sistema debe mostrar placeholders uniformes para secciones en construcción y una página de no encontrado para rutas inexistentes.
- **Criterios de aceptación (EARS):**
  - Cuando el operador acceda a productos, proveedores, movimientos o stock sin implementación (006-009 pendientes), el sistema deberá mostrar un placeholder que incluya el nombre de la sección y el mensaje en español "En construcción" manteniendo la navegación.
  - Si el operador accede a una ruta que no corresponde a ninguna de las cuatro secciones ni a rutas base, el sistema deberá mostrar una página de no encontrado (404) con mensaje en español sin romper el layout.
  - El sistema debe mantener la navegación visible tanto en placeholders como en la página de no encontrado.
  - Si coexisten un error global (RF-4) y un acceso a placeholder o ruta inexistente, el sistema deberá priorizar el error global por encima del placeholder/404.

### RF-3 — Configuración centralizada del cliente de API
El sistema debe centralizar la comunicación HTTP y tomar la URL base de la API exclusivamente desde la configuración de entorno, sin permitir llamadas dispersas.
- **Criterios de aceptación (EARS):**
  - El sistema debe obtener la URL base de la API únicamente desde la variable de entorno definida para el entorno, sin valores hardcodeados en el código.
  - Cuando la aplicación necesite comunicarse con el backend, el sistema deberá usar exclusivamente el cliente centralizado; ningún otro punto del código deberá iniciar llamadas HTTP directas.
  - Si la variable de entorno está ausente, vacía, solo con espacios o no es una URL absoluta http/https válida, el sistema deberá tratarlo como error de configuración según RF-4.
  - Cuando la URL base contenga o no barra final, el sistema deberá normalizarla para evitar barras duplicadas o faltantes al construir la petición.

### RF-4 — Manejo de error global por configuración o API no disponible
El sistema debe informar a nivel de layout cuando la configuración falte o la API no esté disponible al iniciar.
- **Criterios de aceptación (EARS):**
  - Si la URL base no es válida o la API no responde al iniciar (error de red, CORS, timeout superado de 10 segundos), el sistema deberá mostrar un error global a nivel de layout con el mensaje genérico "Error de conexión con el servidor" y opción "Reintentar".
  - Cuando el operador accione "Reintentar" sobre un error global, el sistema deberá volver a intentar la verificación de conectividad sin recargar manualmente el navegador, preservando la ruta actual e historial, y deshabilitando el botón mientras la petición está en curso para evitar reintentos concurrentes.
  - Mientras exista un error global, el sistema deberá mantener la navegación visible, suprimir cualquier estado de sección (cargando/placeholder/vacío) y no mostrar contenido como si fuera carga exitosa.
  - El sistema debe limitar el error global exclusivamente al arranque y a fallos de configuración/conectividad inicial; los fallos posteriores por endpoint durante la navegación deberán manejarse como errores por sección según RF-5 sin escalar a global.

### RF-5 — Componentes base reutilizables de estados (cargando / error / vacío)
El sistema debe proveer patrones uniformes y reutilizables para estados de carga, error y vacío que usarán todas las pantallas futuras.
- **Criterios de aceptación (EARS):**
  - Mientras se espera respuesta de la API por sección, el sistema deberá mostrar un estado de cargando uniforme con texto "Cargando..." accesible, que sustituye al contenido de la sección sin ocultar la navegación.
  - Cuando la respuesta indique lista vacía o sin datos, el sistema deberá mostrar un estado vacío con mensaje en español "Sin datos disponibles", diferenciado visualmente de cargando y de error.
  - Cuando ocurra un error de red, timeout (10s) o 5xx durante una carga por sección, el sistema deberá mostrar un estado de error por sección con mensaje genérico "Error de conexión con el servidor" y botón "Reintentar".
  - Si la API responde con error 4xx, el sistema deberá mostrar el mensaje específico devuelto por la API cuando exista y sea texto en español; si el cuerpo está ausente, vacío, no es JSON o no es español, el sistema deberá mostrar el mensaje genérico de validación "No se pudo completar la solicitud. Revisa los datos e intenta nuevamente." sin exponer detalle técnico, y sin botón Reintentar porque no es recuperable por reintento idéntico.
  - Si la API responde con 401, el sistema deberá tratarlo como cualquier otro 4xx según el criterio anterior, sin redirección ni lógica especial de sesión.
  - Cuando el operador accione "Reintentar" en un estado de error por sección (solo disponible para red/timeout/5xx), el sistema deberá reejecutar exclusivamente la solicitud de esa sección sin perder la sección actual ni su URL, con el botón deshabilitado mientras carga y sin disparar peticiones duplicadas concurrentes.

## Requisitos no funcionales
- **RNF-1 — Mantenibilidad junior:** el esqueleto debe ser comprensible por un desarrollador junior; sin lógica de negocio dispersa en el layout y sin estado global más allá del error de layout de RF-4 implementado con mecanismos del stack mínimo.
- **RNF-2 — Consistencia visual mínima:** estados cargando/error/vacío y navegación deben verse uniformes en toda la app.
- **RNF-3 — Mensajes en español:** toda comunicación visible (navegación, placeholders, errores, vacío) debe estar en español; los dos mensajes genéricos ("Error de conexión con el servidor" y "No se pudo completar la solicitud. Revisa los datos e intenta nuevamente.") deben usarse sin variantes.
- **RNF-4 — Accesibilidad mínima:** HTML semántico (nav, main, button), etiquetas asociadas y navegación por teclado; no se exige WCAG completo.
- **RNF-5 — Desktop-first:** el layout se diseña para escritorio; no se exige adaptación responsive dedicada en el MVP.
- **RNF-6 — Estado en memoria y revalidación:** el estado vive solo en memoria durante la sesión sin persistencia en cliente; todo dato de inventario siempre se revalida contra la API tras la acción que lo afecta (principio frontend §5).

## Casos límite
- Acceso directo por URL a sección en construcción debe mostrar placeholder con nombre de sección, no 404.
- Acceso a ruta inexistente `/ruta-inexistente` debe mostrar 404, no placeholder; si hay error global activo, prevalece el error global.
- Variable de entorno ausente, vacía, solo espacios, sin esquema http/https o con barra duplicada debe tratarse como no válida (error global) y normalizarse cuando sea recuperable.
- API caída, timeout >10s o CORS al cargar la app debe mostrar error global con Reintentar deshabilitado durante carga, no pantalla en blanco.
- Múltiples clics rápidos en Reintentar (global o por sección) deben ignorarse mientras hay petición en curso; no debe haber peticiones concurrentes duplicadas.
- Fallo aislado de un endpoint por sección no debe escalar a error global ni afectar otras secciones con datos ya cargados.
- API devuelve 4xx con cuerpo sin mensaje, vacío, no JSON o en otro idioma: mostrar genérico de validación sin Reintentar.
- API devuelve 4xx con mensaje específico en español: mostrar ese mensaje tal cual, sin mapear a genérico, sin Reintentar.
- API devuelve 5xx, error de red o timeout durante navegación por sección: mostrar "Error de conexión con el servidor" con Reintentar.
- Lista vacía legítima no debe confundirse con error ni con cargando; mostrar "Sin datos disponibles".
- Navegación por teclado debe alcanzar todos los enlaces y botones de Reintentar sin quedar atrapada, incluso con error global visible.
- Reintento exitoso tras error global debe restaurar la sección solicitada sin perder historial de navegación.

## Fuera de alcance
- Funcionalidad de negocio de 006-frontend-productos, 007-frontend-proveedores, 008-frontend-movimientos y 009-frontend-stock (listados, tablas, formularios, filtros, paginación, CRUD, consulta de stock).
- Internacionalización (i18n) y cambio de idioma.
- Tema oscuro / personalización visual y branding definitivo (solo estilos mínimos base).
- Sistema de notificaciones, toasts o alertas globales.
- Autenticación, autorización, manejo de token, login y expiración de sesión; un eventual 401 se trata como 4xx estándar sin redirección.
- Persistencia en cliente (localStorage/sessionStorage) y cache manual de datos de inventario.
- Adaptación responsive dedicada para móvil/tablet y cumplimiento WCAG completo.

## Criterios de finalización
- RF-1 a RF-5 verificados según criterios EARS con navegación persistente, placeholders con nombre de sección y 404 funcionando, priorizando error global cuando corresponda.
- Cliente API centralizado como único punto de HTTP verificado (sin llamadas directas fuera de él), URL base tomada solo de entorno con validación y normalización de barra, y error global con Reintentar probado ante variable faltante/inválida y API caída/timeout 10s.
- Estados base cargando ("Cargando...") / error por sección (dos niveles: 4xx mensaje API o genérico de validación sin Reintentar vs red/timeout/5xx genérico de conexión con Reintentar) / vacío ("Sin datos disponibles") reutilizables, con Reintentar deshabilitado durante carga y sin peticiones duplicadas.
- Fallo aislado por endpoint no escala a global; reintento por sección preserva URL y no pierde sección.
- Accesibilidad mínima (semántica + teclado + aria-current) y mensajes en español verificados manualmente con los dos genéricos sin variantes.
- Sin funcionalidad de negocio de 006-009 incluida y sin persistencia en cliente; revalidación contra API garantizada tras mutación futura.
- Pruebas de componente para layout, navegación, placeholders, 404 y los tres estados con fetch mockeado según frontend §4 / raíz §4: `npm run test` verde y `npm run lint` sin errores.
- Spec aprobada sin [NECESITA ACLARACIÓN] bloqueante.

## Dudas abiertas
- Ninguna bloqueante para este MVP. No hay puntos marcados como [NECESITA ACLARACIÓN]; responsive completo, i18n, tema oscuro y notificaciones se evaluarán en specs futuras si se requieren.
