---
name: sdd-tasks
description: "Genera el prompt para crear specs/00X-nombre/tasks.md a partir de un spec.md y plan.md ya existentes, siguiendo el formato de Spec-Driven Development (SDD) - tareas pequeñas de 20-30 min, en orden de dependencia, cada una con sus RF y un 'Hecho cuando' verificable, con checkboxes. Úsala cuando el usuario diga pasemos o sigamos con las tareas/tasks, genera el tasks.md de X, o hagamos las tareas del spec X dentro de un proyecto que ya tiene su spec.md y plan.md aprobados."
---

# SDD Tasks

Skill para generar el prompt de la etapa de **tareas** dentro de un flujo de
Spec-Driven Development. Esta skill asume que `spec.md` y `plan.md` del spec
en cuestión ya existen y están aprobados — si no es así, avísale al usuario
que faltan esos pasos antes de generar tareas.

## Antes de generar el prompt

1. Identifica el número y nombre exacto del spec (`specs/00X-nombre/`) sobre
   el que se está trabajando, a partir de la conversación.
2. Confirma (o asume razonablemente si es obvio por contexto) que tanto
   `spec.md` como `plan.md` de ese spec ya están generados. Si hay duda
   real, pregúntaselo al usuario con opciones concretas antes de continuar.

## Prompt a generar

Usa exactamente este formato, cambiando solo la ruta del spec:

```
A partir de specs/00X-nombre/spec.md y specs/00X-nombre/plan.md, genera
specs/00X-nombre/tasks.md: tareas pequeñas (máx. 20-30 min cada una), en
orden de dependencia, cada una con los RF que cubre y una línea "Hecho
cuando:" verificable. Usa checkboxes.
```

No agregues nada más al prompt salvo que el usuario pida explícitamente un
ajuste (ej. un tamaño de tarea distinto, o un formato de checklist distinto).

## Revisión del orden de dependencia (después de que el agente responda)

Cuando el agente devuelva el `tasks.md`, revisa si el spec tiene alguna
dependencia de orden no obvia que convenga señalarle al usuario antes de que
empiece a implementar, por ejemplo:
- Corregir una configuración base (ej. build, linter) antes de aplicar
  cambios que dependen de ella.
- Actualizar tests o específicaciones de specs anteriores como última tarea,
  no como primera, si el spec actual modifica un contrato ya validado.
- Tareas de infraestructura (migraciones, variables de entorno) antes que
  tareas de lógica de negocio que dependen de ellas.

Si detectas algo así y el `tasks.md` generado no lo refleja en ese orden,
sugiere pedirle al agente que reordene antes de dar el archivo por bueno.

## Qué NO hace esta skill

No genera `spec.md`, `plan.md`, ni los prompts de clarificación,
implementación o validación — esta skill cubre únicamente la etapa de
tareas. Si el usuario pide continuar con la siguiente etapa después de las
tareas (implementación), indícale que esa es una etapa distinta del proceso
SDD, fuera del alcance de esta skill puntual.