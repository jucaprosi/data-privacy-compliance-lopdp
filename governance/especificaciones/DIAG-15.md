# DIAG-15 · Textos sin jerga en DiagnosticCanvas, aviso de la pregunta objetada y retiro de su excepción
`¤sdd` `¤frontend-ide` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Solo textos de `frontend/src/components/DiagnosticCanvas.tsx` y una lista de excepciones:

- `frontend/tests/textos/excepciones/DIAG-15.txt`: las excepciones que FE-28 dejó para esta ficha. Se borra.

## 2. API

No aplica: no se toca ninguna ruta ni ninguna llamada.

## 3. Reglas

- **R1 · Cinco textos.** Los números de línea son los que anotó la ficha y pueden haberse movido: se buscan por el texto.

  | Texto de hoy | Texto nuevo |
  | :--- | :--- |
  | `title` del temporizador, que nombra una técnica y una «cota» | dice qué mide: el tiempo de la sesión de diagnóstico, de 60 minutos |
  | «timebox» | «tiempo restante» |
  | la etiqueta de la huella | «Huella de integridad (SHA-256)» |
  | «Revisar Respuestas», después del sello real | «Ver respuestas» |
  | la fecha del sello, con el formato del navegador | `toLocaleString("es-EC", { dateStyle: "short", timeStyle: "short" })` |

- **R2 · Textos y un aviso; nada de lógica.** No cambia la lógica del diagnóstico, ni el temporizador, ni el cálculo de la huella, ni quién responde o sella, ni ningún atributo que usen otras pruebas (`data-testid`, roles, nombres accesibles que no sean estos textos). El único elemento nuevo es el aviso de R6.
- **R6 · Aviso de la pregunta objetada (pendiente de DIAG-07).** En el lienzo, una pregunta con una objeción abierta muestra un aviso junto a su enunciado, con `data-testid="pregunta-objetada"`, para quien responde esa dimensión. El aviso solo lee las objeciones que ya entrega `frontend/src/lib/diagnostico/objeciones.ts` (de DIAG-07, que se importa y no se edita). Desaparece cuando la objeción se resuelve al guardar la respuesta. El texto lo fija UX/UI.
- **R7 · Lo que no entra aquí.** Que el botón de sellar y el aviso «Modo lectura» dependan de quién sella, y no de quién responde, es una corrección funcional de DIAG-07 y va en su PR, no en esta ficha.
- **R3 · La excepción desaparece.** Se borra `DIAG-15.txt` y la prueba de textos sin jerga pasa sin ella. La lista de excepciones solo baja.
- **R4 · Secciones ajenas.** El archivo tiene secciones de otras fichas (EVI-01, DIAG-07 y DIAG-11). Esta ficha toca el archivo entero solo cuando DIAG-07 esté fusionada; no escribe dentro de la sección de una ficha que siga abierta.
- **R5 · Los textos los fija UX/UI.** La redacción final del `title` del temporizador la da UX/UI; la tabla de R1 es la propuesta.
- **R-ADPA · Ortogonalidad ZERAG (`DIAG-15`).** Solo frontend.

## 4. Interfaz

Diagnóstico: el temporizador, la etiqueta de la huella, el botón tras el sello y la fecha del sello. Pasa por UX/UI.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** la pantalla del diagnóstico, **entonces** ninguno de los textos antiguos aparece y los nuevos sí. Mutación: restaurar «timebox» hace fallar la prueba. | `frontend/tests/textos/sin-jerga.spec.ts` |
| **Dado** la carpeta de excepciones, **entonces** no existe `DIAG-15.txt` y la prueba estática de textos pasa. Mutación: volver a crear la excepción hace fallar la prueba. | `tests/test_fe28_textos_sin_jerga.py` |
| **Dado** una pregunta con una objeción abierta, **entonces** quien responde su dimensión ve el aviso; al guardar la respuesta, desaparece. Quien no responde esa dimensión no lo ve. Mutación: mostrarlo sin objeción abierta hace fallar la prueba. | `frontend/tests/diagnostico/pregunta-objetada.spec.ts` |
| **Dado** un diagnóstico sellado, **entonces** la fecha del sello se muestra con el formato corto de `es-EC` y el botón dice «Ver respuestas». | `frontend/tests/diagnostico/sellado.spec.ts` |
| **Dado** las suites del diagnóstico, **entonces** siguen pasando sin cambiar lo que afirman, y `tsc --noEmit` y `npm run build` pasan. | `frontend/tests/diagnostico/persistencia.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/DIAG-15.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Origen: nota del Arquitecto ADPA al validar FE-28 (2026-11-08) y textos pendientes de DIAG-11 (UX/UI, 2026-11-09).
- Depende de DIAG-07 (en curso), que posee una sección del mismo archivo y además cambia `sellado.spec.ts` y `persistencia.spec.ts`: DIAG-15 va después.
- **Propiedad que falta en la ficha**, medida en `origin/main` 4eca5af2 y en el PR #772 de DIAG-07 (8e4cd174): `frontend/tests/diagnostico/pregunta-objetada.spec.ts` (crea), y `frontend/tests/diagnostico/sellado.spec.ts`, si la prueba del botón y de la fecha va ahí. La ficha dice que no posee «el spec ni la prueba estática de FE-28», pero lista `sin-jerga.spec.ts` en su propiedad: hay que dejar una sola de las dos cosas.
