---
name: sdd-clarification
description: "Ejecuta la etapa de clarificacion (revision QA) dentro de un flujo de Spec-Driven Development (SDD) sobre un spec.md ya redactado - genera el prompt de revision QA, triangula sus hallazgos entre criticos, menores y sobre-analisis, y arma el prompt de correccion consolidado para el agente. Usala cuando el usuario diga cosas como pasemos o sigamos con la clarificacion, hagamos QA del spec X, revisemos la spec antes de planificar, o cuando pegue el resultado de una revision QA y pida ayuda para interpretarlo o corregirlo."
---

# SDD Clarification

Skill para ejecutar la etapa de **clarificación (QA)** dentro de un flujo de
Spec-Driven Development. Se usa sobre un `spec.md` ya redactado (y, si
aplica, ya con las preguntas de la etapa de especificación respondidas),
antes de pasar a planificación. Es agnóstica del proyecto y del stack —
sirve tanto para specs de backend como de frontend, o de cualquier otro
dominio.

## Paso 1 — Generar el prompt de revisión QA

Identifica la ruta del spec en cuestión y qué documentos de contexto debe
leer el QA para detectar conflictos reales (constitución del proyecto,
`AGENTS.md`, specs prerrequisito o relacionados). Usa este formato exacto,
sin modificarlo — la instrucción de "solo detectar, no proponer soluciones"
es intencional y no debe suavizarse:

```
Revisa <ruta>/spec.md como si fueras un QA muy profesional.
Lista: (1) ambigüedades restantes, (2) contradicciones entre requisitos,
(3) casos límite no cubiertos, (4) conflictos con <documentos de contexto:
constitución, AGENTS.md, specs relacionados/prerrequisito>. No propongas
soluciones todavía: solo detecta. Formato: lista numerada.
```

## Paso 2 — Triaging del resultado (el paso que más valor aporta)

Un QA bien instruido tiende a devolver entre 15 y 25 puntos, y la mayoría de
ellos no ameritan tocar la spec. Antes de escribir cualquier corrección,
clasifica cada punto devuelto en uno de tres baldes, y comunica esa
clasificación al usuario de forma explícita y resumida (no ocultes el
triaje, es la parte más útil de esta skill):

- **Críticos** — contradicciones reales entre requisitos de la misma spec,
  algo que rompería o invalidaría specs ya cerrados/validados, o algo que
  vuelve el spec no-implementable tal como está redactado (ej. un RF que
  exige algo que otro RF prohíbe explícitamente). Estos se resuelven sí o sí
  antes de planificar.
- **Menores** — ambigüedades reales pero que se resuelven con una regla
  simple de una línea, sin mayor debate ni trade-offs complejos.
- **Sobre-análisis** — detalles de implementación que le corresponden al
  `plan.md`, no a la spec: valores exactos (hex, pesos de fuente, timestamps),
  casos de concurrencia de microsegundos, virtualización de listas,
  internacionalización, accesibilidad de borde (`prefers-reduced-motion`),
  formato exacto de mensajes de error. Señálalos como tales explícitamente
  y NO los agregues a la spec — hacerlo mezcla la capa de "qué" con la de
  "cómo" que el proceso SDD busca mantener separadas.

Si una ronda de QA devuelve mayormente sobre-análisis o repite puntos ya
resueltos en una ronda anterior, dilo con claridad y recomienda cerrar la
clarificación ahí — la ambigüedad cero no es un objetivo alcanzable ni
deseable a nivel de spec.

## Paso 3 — Resolver cada punto crítico o menor con una recomendación

Para cada punto que sí amerite corrección, actúa como un ingeniero senior
dando una recomendación concreta con su razonamiento (por qué esa opción y
no las alternativas), priorizando:

1. Consistencia con decisiones ya tomadas en el resto del proyecto (buscar
   el patrón ya usado en specs hermanos antes de inventar uno nuevo).
2. El principio de mínimo alcance viable: ante la duda entre una solución
   simple y una robusta, preferir la simple si no hay un requisito real que
   justifique la complejidad extra.
3. Nunca resolver una ambigüedad de forma que contradiga el propósito
   central del spec. Si una posible corrección (propia o pedida por el
   usuario) haría que el spec pierda su sentido — por ejemplo, "que nada
   cambie" en un spec cuyo objetivo es cambiar algo — no la apliques
   directamente: señala la contradicción, explica la consecuencia práctica,
   y espera confirmación explícita del usuario antes de seguir.

## Paso 4 — Armar el prompt de corrección consolidado

Agrupa todas las correcciones (críticas + menores) en una sola lista
numerada dentro de un único prompt para el agente, cada una con una frase
que indique qué punto(s) del QA resuelve. Cierra siempre el prompt con una
instrucción de verificación antes de dar la spec por cerrada:

```
Corrige <ruta>/spec.md con las siguientes decisiones, resolviendo las
ambigüedades y contradicciones detectadas en la revisión QA:

1. <TÍTULO DE LA DECISIÓN> (resuelve punto(s) X del QA): <explicación de la
   regla concreta a aplicar>.

2. <...siguiente punto...>

El resto de los puntos señalados por el QA corresponden a detalles de
implementación y quedan diferidos a plan.md — no los agregues a la spec.

Muéstrame el diff de los cambios antes de darla por cerrada.
```

## Qué NO hace esta skill

No genera `spec.md` desde cero (eso es la etapa de especificación, anterior
a esta), ni `plan.md`, `tasks.md`, ni los prompts de implementación o
validación. Tampoco decide por sí sola cuándo pasar a planificación — eso
lo confirma el usuario, aunque esta skill puede recomendarlo explícitamente
cuando detecta que una ronda de QA ya no aporta valor nuevo.