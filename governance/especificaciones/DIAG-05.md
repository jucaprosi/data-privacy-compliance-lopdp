# DIAG-05 · «No aplica» con justificación
`¤sdd` `¤diagnostico`

## 1. Datos

Migración `20261030_diagnostico_no_aplica` sobre `diagnostico_respuestas` (`20261024_diagnostico_respuestas`):

- `CHECK estado` pasa de `('Conforme','Parcial','No Conforme','Pendiente')` a `('Conforme','Parcial','No Conforme','Pendiente','No aplica')`.
- Columna nueva `justificacion TEXT NULL`.
- `CHECK ck_resp_no_aplica_justificada`: `estado <> 'No aplica' OR length(trim(justificacion)) >= 20`.
- `justificado_por VARCHAR NULL`, `justificado_en TIMESTAMPTZ NULL` (los pone el servidor cuando `estado = 'No aplica'`).

RLS y permisos sin cambio.

## 2. API

`PUT /diagnostico/respuestas` (`api/routers/diagnostico_respuestas.py`): `RespuestaEntrada.estado` admite `"No aplica"` y suma `justificacion: str | None`.

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 422 | `NO_APLICA_SIN_JUSTIFICACION` | `estado = "No aplica"` con `justificacion` ausente, vacía o de menos de 20 caracteres útiles |
| 422 | (FastAPI) | `justificacion` con `estado ≠ "No aplica"` se ignora y se guarda `NULL` (no es error) |

`GET /diagnostico/respuestas` devuelve `justificacion`, `justificado_por` y `justificado_en`.

## 3. Reglas

- **R1 · Predicado.** `estado = 'No aplica' ⇒ len(trim(justificacion)) ≥ 20`. Se comprueba en el servidor y en la base (`CHECK`).
- **R2 · Scoring.** En `dimensiones_sgpdp.py`, una respuesta `No aplica` **no cuenta** en el denominador de su dimensión (`preguntas_aplicables` baja en uno) y no genera brecha. Si todas las preguntas de una dimensión son `No aplica`, la dimensión queda «sin datos» (`ETIQUETA_SIN_DATOS`), nunca 0 ni 100.
- **R3 · Sellado.** El resultado sellado (DIAG-03) conserva `estado = 'No aplica'` y la justificación en `respuestas`.
- **R4 · Autor.** `justificado_por` = usuario del token; el cuerpo no lo fija.

## 4. Interfaz

`DiagnosticCanvas.tsx`: al elegir «No aplica» aparece un campo obligatorio «¿Por qué no aplica?» con contador (mínimo 20); el botón de guardar se deshabilita hasta cumplirlo; al revisar, la justificación se muestra bajo la pregunta.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** `estado = "No aplica"` sin justificación, **entonces** 422 `NO_APLICA_SIN_JUSTIFICACION`. Mutación: aceptar sin texto hace fallar la prueba (y la `CHECK` de la base la detiene igualmente). | `test_no_aplica_exige_justificacion` |
| **Dado** una justificación de 25 caracteres, **cuando** se guarda y se consulta desde otra sesión, **entonces** vuelve con `justificado_por` del token. | `test_no_aplica_persiste` |
| **Dado** una dimensión con 3 preguntas y 1 `No aplica`, **entonces** `preguntas_aplicables` de esa dimensión es 2 y no hay brecha para esa pregunta. | `test_no_aplica_fuera_del_denominador` |
| **Dado** la pantalla, **cuando** se marca «No aplica» y se escriben 10 caracteres, **entonces** no se puede guardar; con 20, sí. | `frontend/tests/diagnostico/no-aplica.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/DIAG-05.md`. PRD: Módulo 1 («Responder “no aplica” exige justificación escrita»). Invariante: `INV_LOPDP_MULTIDIMENSIONAL_METRICS` (R2). Contraste: D-8.
- Decisión fijada aquí: mínimo de 20 caracteres; cambiable antes de programar.
