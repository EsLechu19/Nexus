---

name: validation-spec
description: Valida una spec completa requisito por requisito, verifica los tests y criterios de finalización, identifica requisitos sin cobertura o con fallos, ejecuta la suite de tests y emite un veredicto basado en la evidencia. No modifica código ni avanza a otra etapa.
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Validation Spec

## Objetivo

Validar de forma completa una `spec.md` ya implementada y determinar si cumple sus requisitos y criterios de finalización.

## Flujo obligatorio

1. Identificar la `spec.md` indicada por el usuario.
2. Leer la spec completa y la documentación necesaria para comprender su alcance.
3. Identificar todos los requisitos, criterios de aceptación y criterios de finalización.
4. Recorrer cada requisito individualmente.
5. Identificar los tests o evidencias que validan cada requisito.
6. Ejecutar los tests correspondientes.
7. Registrar el resultado real de cada test.
8. Determinar para cada requisito si está:

   * Cubierto.
   * Parcialmente cubierto.
   * No cubierto.
9. Ejecutar la suite completa de tests definida por el proyecto.
10. Comprobar todos los criterios de finalización establecidos por la spec.
11. Emitir un veredicto final basado únicamente en la evidencia obtenida.

## Reglas

* No modificar código.
* No modificar tests.
* No modificar `spec.md`.
* No modificar documentación.
* No implementar correcciones.
* No agregar funcionalidades.
* No asumir que un requisito está cubierto si no existe evidencia.
* No considerar un test como válido únicamente porque existe; debe ejecutarse y comprobarse su resultado.
* Si un requisito no tiene un test o evidencia verificable, indicarlo claramente.
* Si un test falla, indicar qué requisito afecta.
* No avanzar a otra etapa del proceso.

## Validación de requisitos

Para cada requisito encontrado en la spec, informar:

```text
Requisito: [ID o descripción]

Tests/Evidencia:
- ...

Resultado:
- ...

Estado:
- Cubierto / Parcialmente cubierto / No cubierto
```

## Validación de tests

Ejecutar la suite de tests definida por el proyecto.

Informar:

```text
Comando:
...

Resultado:
- Tests ejecutados: X
- Tests exitosos: X
- Tests fallidos: X
- Tests omitidos: X
```

No inventar resultados. Utilizar únicamente el resultado real de la ejecución.

## Criterios de finalización

Comprobar uno por uno los criterios de finalización definidos en la spec y marcar:

* ✅ Cumplido
* ⚠️ Parcialmente cumplido
* ❌ No cumplido

Explicar brevemente la evidencia de cada criterio.

## Veredicto

Al finalizar, emitir uno de los siguientes estados:

```text
Cumplida
Parcialmente cumplida
No cumplida
```

El veredicto debe derivarse exclusivamente de los requisitos, tests, evidencias y criterios de finalización comprobados.

## Restricción crítica

Esta Skill es exclusivamente de **validación**.

Si encuentra errores o requisitos incumplidos, debe **reportarlos**, pero no corregirlos.

La ejecución termina después de presentar el informe de validación.
