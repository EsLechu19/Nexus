---

name: implement-task
description: Implementa una única tarea de tasks.md siguiendo la especificación, el plan, las instrucciones del proyecto y la constitución. Usa TDD: primero tests, después implementación. Ejecuta los tests, actualiza tasks.md y se detiene sin comenzar tareas posteriores.
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Implement Task

## Objetivo

Implementar **una única tarea específica** del proyecto siguiendo las reglas y documentos establecidos.

La tarea objetivo debe ser indicada por el usuario, por ejemplo:

* `Implementa T5`
* `Implementa la tarea T5 de specs/005-frontend-base/tasks.md`

## Flujo obligatorio

Antes de modificar código:

1. Identifica la tarea solicitada en `tasks.md`.
2. Lee el contexto necesario para implementarla:

   * `tasks.md`
   * `plan.md`
   * `AGENTS.md`
   * `constitution.md`
   * `spec.md` u otros documentos relacionados, si son relevantes.
3. Identifica los requisitos funcionales (`RF`) relacionados con la tarea.
4. Verifica las restricciones y convenciones que deben respetarse.

## TDD obligatorio

La implementación debe seguir este orden:

### 1. Tests

Escribe primero los tests correspondientes a la tarea.

No implementes el código funcional antes de crear los tests, salvo que el framework requiera una configuración mínima para poder ejecutar dichos tests.

### 2. Implementación

Implementa únicamente el código necesario para que los tests de la tarea pasen.

No agregues funcionalidades pertenecientes a otras tareas.

### 3. Validación

Ejecuta la suite de tests definida por el proyecto.

Por defecto:

```bash
npm run test
```

Si el proyecto establece otro comando en sus documentos, utiliza el comando especificado por el proyecto.

Si existen errores:

* Corrige únicamente los problemas relacionados con la tarea actual.
* Vuelve a ejecutar los tests.
* No continúes con otras tareas.

## Finalización

Cuando la tarea esté correctamente implementada:

1. Marca la tarea como completada en `tasks.md`.
2. Indica qué `RF` cubre la tarea.
3. Resume brevemente:

   * qué se implementó;
   * qué tests se añadieron;
   * resultado de los tests.
4. Detente inmediatamente.

## Restricción crítica

**NO implementes tareas posteriores.**

Si la tarea solicitada es `T5`, el trabajo termina cuando `T5` está implementada y validada.

No comenzar:

```text
T6
T7
T8
...
```

aunque sus dependencias o implementación parezcan sencillas.

## Regla de alcance

Solo modifica archivos necesarios para completar la tarea solicitada.

No realices:

* refactors no relacionados;
* mejoras de código no solicitadas;
* cambios arquitectónicos innecesarios;
* nuevas funcionalidades;
* implementación de tareas posteriores.

Si para completar la tarea es necesario modificar otro archivo, hazlo únicamente si existe una relación directa con la tarea.

## Resultado esperado

La respuesta final debe tener este formato aproximado:

```text
## Tarea implementada

Tarea: T5
Estado: Completada

## RF cubiertos

- RF-XXX
- RF-XXX

## Cambios realizados

- ...
- ...

## Tests

Comando:
npm run test

Resultado:
X tests passed
```

Después de mostrar el resultado, **detenerse**.
