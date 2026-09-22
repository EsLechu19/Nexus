# Validation Spec

Skill para OpenCode que permite **validar una spec completa**, verificando sus requisitos, criterios de aceptación, tests y criterios de finalización definidos en la documentación del proyecto.

## Objetivo

Realizar un proceso controlado de validación que permita determinar, basándose en evidencia real, si una spec está cumplida, parcialmente cumplida o no cumplida.

El flujo es:

```text
Documentación

     ↓

Requisitos

     ↓

Tests / Evidencia

     ↓

Ejecución de Tests

     ↓

Criterios de Finalización

     ↓

Veredicto

     ↓

DETENERSE
```

## Uso

Indica a OpenCode qué spec debe validar:

```text
Valida la spec specs/001-habits-mvp/spec.md
```

También puedes utilizar cualquier otra spec:

```text
Valida la spec specs/005-frontend-base/spec.md
```

La Skill adapta el proceso de validación a la spec indicada.

## Flujo de trabajo

La Skill realiza las siguientes acciones:

1. Lee la `spec.md` completa.

2. Revisa los documentos relevantes del proyecto cuando sean necesarios:

   * `spec.md`
   * `plan.md`
   * `tasks.md`
   * `AGENTS.md`
   * `constitution.md`
   * Tests relacionados.
   * Otros documentos relevantes.

3. Identifica todos los requisitos, criterios de aceptación y criterios de finalización definidos en la spec.

4. Recorre cada requisito individualmente.

5. Identifica qué test o evidencia valida cada requisito.

6. Ejecuta los tests correspondientes.

7. Registra el resultado real de cada test.

8. Determina si cada requisito está:

   * Cubierto.
   * Parcialmente cubierto.
   * No cubierto.

9. Ejecuta la suite completa de tests definida por el proyecto.

10. Comprueba los criterios de finalización de la spec.

11. Identifica cualquier requisito, test o criterio que no esté completamente validado.

12. Emite un veredicto final basado únicamente en la evidencia obtenida.

13. Se detiene.

## Validación requisito por requisito

La Skill debe comprobar cada requisito individualmente.

Para cada uno debe indicar:

```text
Requisito: RF-X

Tests / Evidencia:
- ...

Resultado:
- ...

Estado:
Cubierto / Parcialmente cubierto / No cubierto
```

Si un requisito no tiene ningún test o evidencia verificable, debe indicarlo claramente.

No debe asumir que un requisito está cumplido simplemente porque existe código relacionado.

## Tests

La Skill utiliza el comando de tests establecido por el proyecto.

Por ejemplo:

```bash
npm run test
```

Si el proyecto define otro comando en su documentación, se debe utilizar ese comando.

El resultado debe basarse en la ejecución real de los tests.

La Skill debe informar:

```text
Tests ejecutados: X
Tests exitosos: X
Tests fallidos: X
Tests omitidos: X
```

No debe inventar resultados ni asumir que los tests pasan.

## Criterios de finalización

La Skill también verifica los criterios de finalización definidos por la spec.

Cada criterio debe marcarse como:

```text
✅ Cumplido
⚠️ Parcialmente cumplido
❌ No cumplido
```

La evaluación debe estar acompañada por la evidencia correspondiente.

## Veredicto

Al finalizar la validación, la Skill debe emitir uno de estos estados:

```text
Cumplida
Parcialmente cumplida
No cumplida
```

El veredicto debe basarse exclusivamente en:

* Requisitos validados.
* Tests ejecutados.
* Evidencia encontrada.
* Criterios de aceptación.
* Criterios de finalización.

No debe realizar suposiciones sobre elementos que no hayan podido verificarse.

## Alcance

La Skill está limitada a **validar la spec indicada**.

Durante la validación:

* No implementa funcionalidades.
* No corrige errores.
* No modifica código.
* No modifica tests.
* No modifica `spec.md`.
* No modifica documentación.
* No avanza a otra etapa.

Si encuentra un problema, debe **reportarlo**, no solucionarlo.

Por ejemplo, si encuentra:

```text
RF-5 → Test fallido
```

debe informar el problema y continuar con la validación de los demás requisitos.

No debe modificar el código para hacer que `RF-5` pase.

## Resultado esperado

Al terminar la validación, OpenCode debe presentar un informe similar a:

```text
Spec: specs/001-habits-mvp/spec.md

Requisitos:
- RF-1 → Cubierto
- RF-2 → Cubierto
- RF-3 → Parcialmente cubierto
- RF-4 → No cubierto

Tests:
npm run test

Resultado:
X tests passed
X tests failed

Criterios de finalización:
- Tests → ✅
- Cobertura → ⚠️
- Requisitos → ❌
- Criterios de aceptación → ❌

Veredicto:
No cumplida
```

Después debe **detenerse sin realizar correcciones ni comenzar otra etapa**.

## Estructura

La Skill puede mantenerse con una estructura mínima:

```text
.opencode/
└── skills/
    └── validate-spec/
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

* **Una spec por ejecución.**
* **Validación requisito por requisito.**
* **Evidencia antes que suposiciones.**
* **Tests ejecutados realmente.**
* **Comprobar criterios de finalización.**
* **No modificar código durante la validación.**
* **No corregir problemas encontrados.**
* **No avanzar a otra etapa.**
* **Emitir un veredicto basado en evidencia.**
* **Detenerse al terminar la validación.**
