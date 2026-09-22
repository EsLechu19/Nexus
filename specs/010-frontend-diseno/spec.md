# Spec 010 — Frontend Sistema de Diseño Visual (Aplicación Retroactiva)

## Contexto y objetivo
La tienda dispone de cuatro pantallas funcionales ya construidas y validadas (productos, proveedores, movimientos y stock) más el layout base de `005-frontend-base`. Todas fueron implementadas con foco funcional, de forma que la identidad visual es inconsistente y se ha detectado que las clases de utilidad del sistema de estilos no se están aplicando correctamente en el build. Esta funcionalidad no agrega ningún comportamiento ni requisito funcional nuevo: define y aplica retroactivamente la identidad visual (paleta, tipografía, espaciado y estilos de componentes) de forma consistente en toda la aplicación, corrigiendo la aplicación del sistema de estilos para que las clases utilitarias se rendericen efectivamente.

En este spec, **LO YA VALIDADO PERMANECE INTACTO** significa que el **COMPORTAMIENTO FUNCIONAL** de los componentes ya validados (qué endpoint llaman, qué texto muestran en cada caso, cuándo se habilita/deshabilita un botón, la lógica de validación y manejo de errores) debe permanecer intacto. El **ASPECTO VISUAL** (color, tipografía, espaciado, clases CSS) SÍ puede y debe cambiar — ese es el objetivo de este spec. Los tests existentes que dependan de clases CSS específicas en vez de comportamiento/contenido visible deben actualizarse como parte de este spec, no evitarse. El badge de alerta de `009-frontend-stock` puede cambiar su clase de color (ej. de `bg-red-50` a un nuevo token semántico de error), siempre que el criterio de negocio (leer el campo `alerta` del backend, nunca recalcularlo) se mantenga sin cambios.

## Usuarios
- **Encargado de tienda / Operador:** utiliza diariamente las cuatro pantallas para gestionar inventario. Es el mismo actor de `005`/`006`/`007`/`008`/`009`; percibe la mejora como mayor coherencia, legibilidad y jerarquía visual sin cambiar flujos.
- **Equipo de producto (usuario indirecto):** necesita una base visual consistente para evolucionar el producto sin deuda de estilos hardcodeados.

## Historias de usuario
- **HU-1:** Como encargado, quiero ver una identidad visual coherente en las cuatro pantallas y el layout (misma paleta, tipografía y espaciado) para percibir la aplicación como un producto unificado.
- **HU-2:** Como encargado, quiero distinguir con claridad la jerarquía de acciones (primaria/secundaria/peligro) en botones para saber qué acción es principal en cada contexto sin cambiar su comportamiento.
- **HU-3:** Como encargado, quiero que tablas, inputs, modales, badges de alerta y banners de éxito/error se vean uniformes y legibles para escanear información rápidamente.
- **HU-4:** Como encargado, quiero que lo que veo en desarrollo sea lo que se publica en el build, sin estilos que desaparecen o se ven distintos por un problema de configuración del sistema de estilos.

## Requisitos funcionales

### RF-1 — Identidad visual base consistente (paleta, tipografía, espaciado)
El sistema debe exponer una identidad visual única y consistente en toda la aplicación, sin alterar comportamientos funcionales ya validados.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado acceda a cualquier pantalla (productos, proveedores, movimientos, stock) o al layout base, el sistema deberá presentar la misma paleta gamer colorida con tono profesional sobrio, la misma familia tipográfica Inter y la misma escala de espaciado de 4px, sin variaciones por pantalla.
  - El sistema deberá aplicar la paleta de forma semántica y consistente: un color primario para acciones principales y navegación activa, un color neutro para fondos y bordes, y colores semánticos para éxito/error/alerta (incluido `Bajo stock`), sin introducir nuevos colores por pantalla.
  - El sistema deberá usar Inter como tipografía única para encabezados, cuerpo y controles, con jerarquía definida (tamaño/peso) consistente en las cuatro pantallas. Si Inter no carga por cualquier motivo, se debe usar una pila de fuentes de respaldo del sistema (ej. `system-ui, sans-serif`), para que la app nunca quede sin tipografía legible.
  - El sistema deberá respetar la escala de espaciado de 4px para márgenes, paddings y gaps en todas las vistas, de forma que dos elementos equivalentes en pantallas distintas tengan el mismo espaciado.
  - El sistema no deberá introducir estilos hardcodeados que contradigan la identidad (ej. colores hexadecimales dispersos o fuentes distintas por componente).

  > Nota: Los valores exactos (códigos hexadecimales, escala de espaciado en px, pesos y tamaños de tipografía, mapeo de clases por componente) se definen en `plan.md`, no en la spec. La spec solo establece el QUÉ (paleta profesional sobria con acento violeta/gaming, tipografía Inter, escala base 4px, prioridad de aplicación) y el POR QUÉ.

### RF-2 — Tablas con estilo uniforme (prioridad 1)
El sistema debe presentar todas las tablas de listado (productos 4 cols, proveedores 5 cols, movimientos 7 cols, stock 5 cols) con el mismo lenguaje visual.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado consulte cualquier listado, el sistema deberá mostrar la tabla con cabeceras con tipografía y color uniformes, filas con separación y alineación consistentes, y scroll vertical preservado, sin cambiar el orden, paginación o filtrado ya validado.
  - Cuando una fila esté en estado de alerta (stock `alerta == true`), el sistema deberá mantener el badge textual `"Bajo stock"` como fuente de verdad accesible y el refuerzo visual de fila ya validado, pero ahora con los tokens de color/espaciado de la identidad, sin depender solo de color.
  - El sistema no deberá truncar contenido de celdas de forma distinta por pantalla; `nombre`/`codigo` mantienen salto de línea ya validado.

### RF-3 — Botones con jerarquía visual (prioridad 1)
El sistema debe distinguir visualmente la jerarquía de botones sin cambiar su comportamiento ya validado.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado vea cualquier pantalla, el sistema deberá distinguir botón primario (ej. "Crear producto/movimiento", "Reintentar" en error de conexión) con estilo de mayor peso visual, botón secundario (ej. "Cancelar") con peso menor, y botón de peligro (ej. "Dar de baja") con estilo de peligro, de forma consistente en las cuatro pantallas.
  - Mientras un botón esté en estado `disabled` (durante `cargando` ya validado), el sistema deberá mostrar un estado deshabilitado visualmente coherente en todas las pantallas, sin cambiar la lógica de deshabilitado ya validada.
  - El sistema deberá mantener el foco visible para navegación por teclado en todos los botones con el mismo estilo de anillo de foco en toda la app.

### RF-4 — Inputs y modales/diálogos (prioridad 2)
El sistema debe presentar inputs y contenedores modales de forma uniforme, reutilizando el mismo lenguaje ya validado para formularios.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado abra cualquier modal de alta/edición o diálogo de baja (productos, proveedores, movimientos), el sistema deberá mostrar inputs con mismo estilo de borde, fondo, padding y tipografía, y con el mismo tratamiento de estado de error de forma (ya validado: `"Campo requerido"` / `"Debe ser un número..."`).
  - Cuando un modal/diálogo esté abierto, el sistema deberá presentar el overlay y el contenedor con el mismo espaciado, bordes y jerarquía de títulos en las cuatro pantallas, sin cambiar el comportamiento de apertura/cierre ya validado (incluido `ESC` ignorado durante `cargando`).
  - El sistema deberá mantener la asociación `label`/`input` y el foco visible ya validados, ahora con los tokens tipográficos y de espaciado de la identidad.

### RF-5 — Badges y banners (prioridad 3)
El sistema debe presentar badges de alerta y banners/mensajes con estilo consistente, heredando los colores semánticos ya definidos.
- **Criterios de aceptación (EARS):**
  - Cuando `alerta == true` en stock, el sistema deberá mostrar el badge `"Bajo stock"` y la fila marcada con los mismos tokens de color y espaciado en toda la app, nunca solo color sin badge.
  - Cuando `alerta == false`, el sistema deberá mostrar `"—"` en la columna `alerta` sin marca visual, con el mismo estilo de celda en todas las filas.
  - Cuando el sistema muestre un banner de éxito (`"Producto creado..."`, `"Movimiento registrado..."`) o un `ErrorMessage`/`EmptyState`/`Loading`, el sistema deberá presentarlos con la misma tipografía, espaciado y colores semánticos (éxito/error/alerta) en las cuatro pantallas, sin cambiar su duración, posición o variante ya validada (4xx sin Reintentar vs 5xx con Reintentar).

### RF-6 — Corrección de la aplicación del sistema de estilos en el build
El sistema debe garantizar que las clases de utilidad del sistema de estilos se apliquen efectivamente tanto en desarrollo como en el build de producción, sin cambiar ningún comportamiento funcional.
- **Criterios de aceptación (EARS):**
  - Cuando el encargado ejecute la aplicación en desarrollo y en el build de producción, el sistema deberá renderizar los mismos estilos (colores, tipografía, espaciado) sin diferencias visibles por purga o falta de configuración.
  - Si existían clases utilitarias usadas en las cuatro pantallas que no se aplicaban por configuración, el sistema deberá aplicarlas correctamente tras la corrección, sin necesidad de reescribir la arquitectura de componentes ya validada.
  - El sistema deberá eliminar estilos hardcodeados o inconsistentes que contradigan los tokens de la identidad y reemplazarlos por los tokens definidos, sin modificar la lógica de negocio ya validada.

## Requisitos no funcionales
- **RNF-1 — Sin regresión funcional:** ningún RF ya validado en `005`/`006`/`007`/`008`/`009` debe cambiar de comportamiento; solo cambia la capa visual. Verificación: `npm run test` sigue verde.
- **RNF-2 — Consistencia:** un mismo componente visual (botón primario, input, `th`, badge, `Loading`/`ErrorMessage`/`EmptyState`) debe verse idéntico en las cuatro pantallas. Verificación: revisión visual cruzada.
- **RNF-3 — Mantenibilidad:** la identidad se define una sola vez como tokens semánticos (paleta, Inter, escala 4px) y se consume de forma consistente; no se duplican valores hexadecimales o tamaños por pantalla. Verificación: búsqueda de valores hardcodeados.
- **RNF-4 — Accesibilidad preservada:** el contraste del nuevo color de fila/badge debe mantener legibilidad y el badge textual sigue siendo la fuente de verdad para lector de pantalla (no solo color). Verificación: revisión `role`/`aria` ya validada.
- **RNF-5 — Idioma:** mensajes visibles siguen en español, sin cambios. Verificación: revisión manual.
- **RNF-6 — Build determinista:** el resultado del build no depende de orden de importación de estilos; las clases purgadas deben incluir las usadas en las cuatro pantallas. Verificación: `npm run build` sin diferencias visuales.
- **RNF-7 — Purga segura de Tailwind:** ningún componente debe construir nombres de clases Tailwind de forma dinámica mediante concatenación de strings (ej. `"bg-" + color`); en su lugar, se debe usar un objeto de mapeo completo con todas las combinaciones posibles de clases ya escritas de forma literal, para evitar que el proceso de purga de producción elimine clases que Tailwind no puede detectar estáticamente. Verificación: búsqueda de concatenación dinámica de clases.

  > Nota: Definir tokens de diseño en `tailwind.config.js` y ajustar `postcss.config.js` es parte esperada del alcance de este spec (configuración del stack ya elegido `frontend/docs/constitution.md:3`), no es una "dependencia nueva" en el sentido de `frontend/AGENTS.md:27` y no requiere aprobación adicional más allá de la de este spec.

## Casos límite
- Pantalla con tabla vacía (`EmptyState`) debe mostrar el mismo estilo de vacío en las cuatro secciones, sin perder el nuevo espaciado/tipografía.
- Fila en alerta (`alerta == true`) con `stock_minimo 0` nunca ocurre por contrato (backend `alerta false` si `stock_minimo 0`), pero si ocurriera por dato corrupto omitido, la fila ya estaría omitida por `esFilaStockValida` y no se pinta.
- Modal con error de forma (`"Campo requerido"`) debe mostrar el mismo estilo de borde/error en productos, proveedores y movimientos.
- Botón `Reintentar` en estado `cargando` debe verse deshabilitado con el mismo estilo en las cuatro pantallas y en el banner global.
- Si una pantalla tenía estilo inline hardcodeado que coincidía casualmente con el token, debe migrarse igual al token para evitar divergencia futura.
- Build de producción con purga: una clase usada solo en `stock` (ej. `bg-red-50` para fila en alerta) no debe ser purgada por no estar presente en otras pantallas.
- Navegación por teclado debe seguir mostrando el mismo anillo de foco con los nuevos colores en toda la app.

## Fuera de alcance
- Nueva funcionalidad, cambio de flujos, validaciones, ordenamientos, filtros, paginación o endpoints; todo lo ya validado permanece intacto.
- Modo oscuro / tema claro alternativo, cambio de paleta por usuario o por sección.
- Adaptación responsive dedicada para móvil/tablet más allá del `Desktop-first` ya declarado en `005`.
- Animaciones complejas, transiciones elaboradas, iconografía nueva más allá de la paleta/tipografía/espaciado.
- Branding definitivo (logo, ilustraciones) o librería de componentes externa adicional.
- Internacionalización (i18n) y cambio de idioma.

## Criterios de finalización
- RF-1 a RF-6 verificados según EARS: paleta gamer colorida con tono profesional sobrio, Inter y escala 4px aplicados en las cuatro pantallas y layout base; tablas 4/5/7/5 cols, botones (primario/secundario/peligro), inputs/modales y badges/banners con estilo consistente — los tres grupos deben estar igualmente completos y verificados, sin importar el orden en que se implementaron (el orden tablas-botones > inputs-modales > badges-banners es guía de secuencia para `plan.md`/`tasks.md`, no criterio de cumplimiento); corrección del sistema de estilos verificada en `dev` y `build` sin regresión.
- Sin estilos hardcodeados que contradigan los tokens (búsqueda de hexadecimales dispersos vacía) y sin clases utilitarias purgadas indebidamente.
- `npm run test` verde (sin cambios funcionales) y `npm run lint` sin errores.
- `npm run dev` y `npm run build` + preview muestran la misma identidad visual en las cuatro pantallas, con scroll, modales y estados `Loading`/`EmptyState`/`ErrorMessage` ya validados preservados.
- Spec aprobada sin [NECESITA ACLARACIÓN] bloqueante.

## Dudas abiertas
- Ninguna bloqueante. No hay puntos marcados como [NECESITA ACLARACIÓN]; la definición de tokens semánticos exactos (códigos hex de primario/neutro/éxito/error/alerta) se documentará en el plan si se requiere detalle, pero no bloquea la spec.
