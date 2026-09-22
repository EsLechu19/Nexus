# Implement Task

Skill para OpenCode que permite implementar **una única tarea** definida en `tasks.md`, siguiendo las especificaciones, restricciones y arquitectura establecidas en la documentación del proyecto.

## Objetivo

Automatizar un flujo controlado de implementación basado en **TDD**, evitando que el agente avance accidentalmente hacia tareas posteriores.

El flujo es:

```text
Documentación
     ↓
Tests
     ↓
Implementación
     ↓
Validación
     ↓
Actualizar tasks.md
     ↓
Informar RF
     ↓
DETENERSE
```

## Uso

Indica a OpenCode qué tarea debe implementar:

```text
Implementa T5 de specs/005-frontend-base/tasks.md
```

También puedes utilizar cualquier otra tarea:

```text
Implementa T3 de specs/002-auth/tasks.md
```

La Skill adapta el flujo a la tarea indicada.

## Flujo de trabajo

La Skill realiza las siguientes acciones:

1. Lee la tarea solicitada en `tasks.md`.
2. Revisa los documentos relevantes del proyecto:

   * `tasks.md`
   * `plan.md`
   * `AGENTS.md`
   * `constitution.md`
   * `spec.md`
   * Otros documentos relevantes cuando sea necesario.
3. Identifica los requisitos funcionales (`RF`) relacionados.
4. Escribe primero los **tests**.
5. Implementa el código necesario para que los tests pasen.
6. Ejecuta la suite de tests definida por el proyecto.
7. Corrige errores relacionados únicamente con la tarea actual.
8. Marca la tarea como completada en `tasks.md`.
9. Informa los `RF` cubiertos y el resultado de los tests.
10. Se detiene.

## TDD

La Skill sigue este orden:

```text
Tests
  ↓
Implementación
  ↓
Tests
  ↓
Validación
```

No debe implementar primero la funcionalidad y crear los tests después.

## Alcance

La Skill está limitada a **una sola tarea por ejecución**.

Por ejemplo, si se solicita:

```text
Implementa T5
```

la Skill puede modificar todo lo necesario para completar `T5`, pero **no debe comenzar `T6`**, aunque:

* `T6` sea sencilla.
* `T6` dependa de `T5`.
* `T6` parezca necesaria.
* Queden cambios relacionados pendientes.

El flujo termina cuando `T5` ha sido implementada y validada.

## Validación

La Skill utiliza el comando de tests establecido por el proyecto.

Por ejemplo:

```bash
npm run test
```

Si el proyecto define otro comando en su documentación, se debe utilizar ese comando.

El resultado de la ejecución se informa al finalizar.

## Resultado esperado

Al terminar una tarea, OpenCode debe informar:

```text
Tarea: T5
Estado: Completada

RF cubiertos:
- RF-XXX

Tests:
npm run test

Resultado:
X tests passed
```

Y después debe **detenerse sin iniciar otra tarea**.

## Estructura

La Skill puede mantenerse con una estructura mínima:

```text
.opencode/
└── skills/
    └── implement-task/
        ├── SKILL.md
        └── README.md
```

### Archivos

| Archivo     | Propósito                          |
| ----------- | ---------------------------------- |
| `SKILL.md`  | Instrucciones que sigue el agente  |
| `README.md` | Documentación para desarrolladores |

`README.md` es opcional para el funcionamiento de la Skill, mientras que `SKILL.md` contiene las instrucciones principales.

## Principios

* **Una tarea por ejecución.**
* **Tests antes que implementación.**
* **Seguir la documentación del proyecto.**
* **No introducir cambios fuera del alcance.**
* **Validar antes de finalizar.**
* **Actualizar `tasks.md`.**
* **Informar los RF cubiertos.**
* **Detenerse al terminar la tarea.**
