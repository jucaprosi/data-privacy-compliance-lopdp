# DIAG-08 · Escala SMARTCIDI en el servidor
`¤sdd` `¤diagnostico` `¤diagnostico-scoring`

## 1. Datos

Migración `20261031_diagnostico_escala_smartcidi`, sobre `diagnostico_respuestas` (DIAG-03):

| Cambio | Detalle |
| :--- | :--- |
| Columna nueva `nivel_asignado` | `SMALLINT NULL`, `CHECK (nivel_asignado BETWEEN 1 AND 5)`; `NULL` = la pregunta aún no se respondió con la escala nueva |
| `ck_diag_evidencia` | pasa de `nivel_evidencia BETWEEN 0 AND 3` a `BETWEEN 0 AND 4` |
| Filas existentes | evidencia: `1 → 2`, `2 → 3`, `3 → 4` (E1 documentada → documental, E2 implementada → operativa, E3 probada → revisada); `0` no cambia. `nivel_asignado` queda `NULL`: no se puede deducir si un «Parcial» era 2 o 3 |
| `downgrade` | evidencia `4 → 3`, `3 → 2`, `2 → 1`, `1 → 0` (con pérdida, documentada en la migración); se elimina `nivel_asignado` |

`lopdp_app` conserva sus permisos; RLS sin cambios. `diagnostico_resultados` no se altera: los resultados sellados son inmutables y su JSON `indicadores` conserva la forma con que se sellaron.

**Escala** (hojas «Niveles de Madurez» y «Catálogos» del archivo SMARTCIDI), como constantes del dominio:

| Nivel asignado | Nombre | Criterio operativo |
| :--- | :--- | :--- |
| 1 | Inicial / Reactivo | No existe o se gestiona informalmente |
| 2 | Básico / Repetible | Prácticas aisladas o documentos iniciales |
| 3 | Definido / Documentado | Políticas, matrices, procedimientos y responsables definidos |
| 4 | Gestionado / Demostrable | Se aplica, se revisa, tiene seguimiento y métricas |
| 5 | Optimizado / Mejora continua | Integrado a gobierno, riesgos y seguridad, con mejora demostrable |

| Nivel de evidencia | Nombre |
| :--- | :--- |
| 0 | Verbal: sin evidencia |
| 1 | Informal: correo, captura, práctica no formalizada |
| 2 | Documental: política, matriz, procedimiento, contrato |
| 3 | Operativa: registros de aplicación |
| 4 | Revisada: auditada o revisada por la dirección |

`IndicadoresSellados` (forma nueva, `escala = "smartcidi_1_5"`): `{escala, cumplimiento: bool, brechas_criticas: int, brechas_altas: int, por_dimension: [{dimension, nombre, nivel: int 0–5, etiqueta, score: float, cobertura: float, brechas_criticas, brechas_altas}], respaldo_documental: float, preguntas_evaluadas, preguntas_aplicables, cobertura}`. Desaparecen `madurez`, `nivel_madurez` y `riesgo_residual`.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `PUT /diagnostico/respuestas` | los de hoy (DIAG-03; DIAG-07 los cambia después) | por pregunta `{"pregunta_id": int, "nivel_asignado": 1–5, "nivel_evidencia": 0–4}`; `estado` en el cuerpo → 422 | `200` con `estado` derivado (R3) |
| `GET /diagnostico/respuestas` | sin cambio | — | cada fila con `nivel_asignado`, `nivel_evidencia` y `estado` derivado |
| `POST /diagnostico/resultados` (sellar) | `dpo` | sin cambio | `201` con `indicadores` en la forma nueva |
| `GET /diagnostico/resultados` | sin cambio | — | cada resultado con `indicadores.escala`: `"smartcidi_1_5"` o, si el JSON sellado no la trae, `"anterior"` (se añade al leer, sin escribir) |
| Informes de `api/routers/diagnostico.py` | sin cambio | sin cambio | niveles por dimensión; ninguna madurez 0–3 ni cifra global |

Valores fuera de escala: 422 de validación del esquema.

## 3. Reglas

- **R1 · Nivel efectivo.** `efectivo = min(nivel_asignado, nivel_evidencia_sellado + 1)`. Sin documento vinculado, `nivel_evidencia_sellado = 0` (regla de sellado de DIAG-03, ahora en 0–4). Sin el reescalado `× 4/3` actual.
- **R2 · Puntaje y riesgo por control.** `score = efectivo / 5 × criticidad`; `riesgo_brecha = (5 − efectivo) × criticidad`; crítico si `≥ 15`, alto si `≥ 9` (umbrales actuales).
- **R3 · Estado derivado.** `nivel_asignado = 1 ⇒ No Conforme`; `2 ≤ nivel_asignado ≤ 3 ⇒ Parcial`; `nivel_asignado ≥ 4 ⇒ Conforme`; `NULL ⇒ Pendiente`. Es la única fuente del campo `estado`; el hallazgo automático por «no» o «parcial» en un control obligatorio (PRD, Módulo 1) sigue leyéndolo.
- **R4 · Nivel por dimensión.** `score_dimension = Σ score / Σ criticidad × 100` sobre los controles aplicables; nivel por rangos `0–39 → 1`, `40–59 → 2`, `60–74 → 3`, `75–89 → 4`, `90–100 → 5`; los topes por control estructural degradado y por evidencia insuficiente se aplican **dentro de la dimensión**; `0` con la etiqueta «Sin evaluación suficiente» cuando la cobertura no alcanza (regla actual del motor).
- **R5 · Sin cifra global.** Ningún indicador del sellado ni ningún informe combina dimensiones en un puntaje, nivel o porcentaje de la organización (`INV_LOPDP_MULTIDIMENSIONAL_METRICS`). `cumplimiento` es booleano (`brechas_criticas = 0`) y `respaldo_documental = media(nivel_evidencia_sellado) / 4 × 100` describe la evidencia, no la madurez.
- **R6 · Pendientes.** Una pregunta aplicable con `nivel_asignado NULL` computa como pendiente (cero), igual que una sin respuesta.
- **R7 · Sin motor 0–3.** Ningún módulo de `features/diagnostico/` conserva `madurez_spdp` ni las etiquetas «Caótico», «Implícito», «Temprano explícito» o «Maduro explícito».

## 4. Interfaz

Sin interfaz: la pantalla de respuesta es de DIAG-09 y el tablero de FE-24.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una respuesta con nivel asignado 4 y evidencia 4 con documento, **entonces** el nivel efectivo es 4 y el estado «Conforme»; **y** con asignado 2, efectivo 2 y estado «Parcial». Mutación: volver a la tabla de tres estados hace fallar la prueba. | `test_nivel_asignado_tal_cual` |
| **Dado** asignado 5 y evidencia 2 con documento, **entonces** efectivo 3; **y** sin documento, evidencia sellada 0 y efectivo 1. | `test_evidencia_acota_nivel` |
| **Dado** un cuerpo con `estado` o con `nivel_asignado = 6`, **entonces** 422. | `test_escala_validada` |
| **Dado** una dimensión con controles evaluados, **cuando** el `dpo` sella, **entonces** `indicadores.por_dimension` trae su nivel 1–5 y su etiqueta, **y** `indicadores` no contiene `madurez`, `nivel_madurez` ni `riesgo_residual`. | `test_indicadores_por_dimension` |
| **Dado** un resultado sellado antes de la migración, **cuando** se consulta, **entonces** `indicadores.escala = "anterior"` y su huella sigue verificando la cadena. | `test_resultado_anterior_legible` |
| **Dado** filas de respuesta con evidencia 1, 2 y 3, **cuando** se migra, **entonces** quedan en 2, 3 y 4 con `nivel_asignado NULL`, **y** una pregunta así computa como pendiente. | `test_migracion_escala` |
| **Dado** respuestas de A, **cuando** se consultan en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_respuestas_escala` |
| **Dado** el código de `features/diagnostico/`, **entonces** no aparece `madurez_spdp` ni las etiquetas de la escala 0–3. | `test_sin_motor_cero_tres` |

Todas en `tests/test_diagnostico_escala_smartcidi.py`, contra una rama Neon de revisión.

## 6. Trazabilidad

- Ficha: `governance/tareas/DIAG-08.md`. PRD: Módulo 1 («Scoring multidimensional cuádruple», «Escala y cota»), criterio 2. Invariante: `INV_LOPDP_MULTIDIMENSIONAL_METRICS`. Fuente: archivo de assessment SMARTCIDI, hojas «Niveles de Madurez», «Catálogos» y «Guía Aplicación Comercio».
- La siguen DIAG-09 (pantalla), FE-24 (tablero), DIAG-06 (comparativo) y ORG-15 (cartera), que leen la forma nueva de los indicadores.
