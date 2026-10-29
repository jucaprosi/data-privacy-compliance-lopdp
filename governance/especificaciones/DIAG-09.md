# DIAG-09 · Escala SMARTCIDI en la pantalla
`¤sdd` `¤diagnostico` `¤frontend-ide`

## 1. Datos

Sin datos persistentes. Lee y escribe con la API de DIAG-08 (`governance/especificaciones/DIAG-08.md`): `PUT /diagnostico/respuestas` con `nivel_asignado` (1–5) y `nivel_evidencia` (0–4); `GET /diagnostico/respuestas` con `estado` derivado; `GET /diagnostico/resultados` con `indicadores.escala` y `indicadores.por_dimension`.

`frontend/src/lib/diagnostico/escala.ts` exporta las dos tablas de la escala (nivel, nombre y criterio; escalón de evidencia y nombre) con los textos de DIAG-08 §1. Es la única copia en el frontend.

## 2. API

Sin API nueva.

## 3. Reglas

- **R1 · Una sola copia de la escala.** Ningún otro archivo del frontend define los cinco niveles ni los cinco escalones.
- **R2 · El estado es derivado.** La pantalla no envía `estado`; muestra el que devuelve el servidor con las etiquetas de `estadosCumplimiento.ts` («Implementado», «Parcial», «No implementado», «Pendiente»).
- **R3 · Sin cifra global.** Ningún elemento del panel ejecutivo ni del reporte del navegador muestra un puntaje, nivel o porcentaje de la organización; los puntajes y niveles se muestran por dimensión (`INV_LOPDP_MULTIDIMENSIONAL_METRICS`).
- **R4 · Escala anterior.** Si `indicadores.escala = "anterior"`, se muestra «Este diagnóstico se selló con la escala anterior. Vuelve a responder y sellar para ver los niveles por dimensión.» y no se dibujan niveles.
- **R5 · Pendientes por migración.** Una pregunta con `nivel_asignado` nulo se muestra sin nivel seleccionado y cuenta como pendiente en el avance.

## 4. Interfaz

Pregunta del assessment: «1. Nivel de madurez» con cinco opciones en una fila (nombre corto y, debajo, el criterio de la opción enfocada o seleccionada; navegables con teclado, `role="radiogroup"`); «2. Evidencia» con cinco escalones, con el aviso actual cuando no hay documento vinculado (se sella como 0). Panel ejecutivo: una fila por dimensión con su nivel y etiqueta; sin barras de porcentaje de la organización.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una pregunta del assessment, **entonces** se ven cinco niveles con su criterio y cinco escalones de evidencia; **y** elegir el nivel 2 envía `nivel_asignado: 2` sin `estado`. Mutación: volver a tres botones hace fallar la prueba. | `diagnostico/escala.spec.ts › cinco niveles` |
| **Dado** la API devuelve `estado: "Parcial"` para el nivel 3, **entonces** la pregunta muestra «Parcial» como dato, no como botón. | `diagnostico/escala.spec.ts › estado derivado` |
| **Dado** un resultado con `por_dimension`, **entonces** el panel muestra un nivel por dimensión y el texto no contiene «Puntaje según respuestas» ni un porcentaje de la organización. | `diagnostico/escala.spec.ts › sin cifra global` |
| **Dado** un resultado con `escala: "anterior"`, **entonces** aparece el aviso de R4 y ningún nivel. | `diagnostico/escala.spec.ts › escala anterior` |
| **Dado** respuestas con `nivel_asignado` nulo, **entonces** se muestran sin selección y el avance las cuenta como pendientes. | `diagnostico/escala.spec.ts › pendientes por migración` |

## 6. Trazabilidad

- Ficha: `governance/tareas/DIAG-09.md`. PRD: Módulo 1 («Scoring multidimensional cuádruple»), Doctrina 4. Invariante: `INV_LOPDP_MULTIDIMENSIONAL_METRICS`. Depende de DIAG-08 (API y escala).
