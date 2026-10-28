# MTGE-03 · EIPD guiada de ocho pasos con asistente de obligatoriedad, decisión documentada e informe final
`¤sdd` `¤riesgos-eipd` `¤mtge-granescala` `¤hallazgos`

## 1. Datos

Migración `20261105_eipd_guiada`: `eipd (id, tenant_id, tratamiento_id, obligatoria BOOLEAN, motivo_obligatoriedad TEXT, paso_actual SMALLINT, consulta_titulares TEXT NULL, ciclo_vida JSONB, necesidad TEXT, riesgo_inherente VARCHAR(8), riesgo_residual VARCHAR(8) CHECK (IN ('bajo','medio','alto')), decision VARCHAR(16) NULL CHECK (IN ('aceptar','medidas','consulta_previa')), decision_texto TEXT NULL, informe_sha256 NULL, cerrada_en NULL, creado_por, creado_en)` y `eipd_incumplimientos (id, tenant_id, eipd_id, texto, hallazgo_id)`. RLS ENABLE y FORCE.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `POST /eipd` | `implementador`, `coordinador` | `{tratamiento_id}` | `201 Eipd` con `obligatoria` calculada |
| `PUT /eipd/{id}/paso/{n}` | `implementador`, `coordinador` | cuerpo del paso | `200` |
| `POST /eipd/{id}/cerrar` | `implementador` | — | `200 {informe_sha256}` |
| `GET /eipd?tratamiento_id=` | lectura (incluido `dpo`) | — | `200` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 409 | `EIPD_OBLIGATORIA` | marcar `obligatoria = false` cuando MTGE la exige |
| 409 | `EIPD_SIN_DECISION` | cerrar con `riesgo_residual = alto` y sin `decision` |
| 409 | `EIPD_PASO_INCOMPLETO` | cerrar con pasos 1–7 incompletos |

## 3. Reglas

- **R1 · Obligatoriedad.** `obligatoria = mtge(tratamiento) ∨ marcar_eipd(tratamiento, RAT-05) ∨ decisión manual`; nunca puede ponerse en `false` si MTGE la exige.
- **R2 · Incumplimientos ⇒ hallazgos.** Cada ítem del paso 5: `registrar_hallazgo(origen='eipd', origen_ref=f"{eipd_id}:{n}", severidad='alta')`.
- **R3 · Cierre.** `cerrar ⇒ pasos 1..7 completos ∧ (riesgo_residual ≠ 'alto' ∨ decision IS NOT NULL)`; genera el informe y lo custodia.
- **R4 · Consulta previa (*).** `decision = 'consulta_previa'` solo deja constancia; el procedimiento ante la SPDP queda para LEG-03.

## 4. Interfaz

Riesgos y auditoría › Evaluaciones de impacto: lista por tratamiento con estado; asistente de ocho pasos; en el 7, tarjetas de decisión; en el 8, informe descargable.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un tratamiento con MTGE obligatorio, **cuando** se marca no obligatoria, **entonces** 409 `EIPD_OBLIGATORIA`. | `test_eipd_obligatoria_por_mtge` |
| **Dado** residual alto sin decisión, **cuando** se cierra, **entonces** 409 `EIPD_SIN_DECISION`. Mutación: cerrar igual hace fallar la prueba. | `test_eipd_residual_alto_decision` |
| **Dado** 2 incumplimientos en el paso 5, **entonces** hay 2 hallazgos `eipd`. | `test_eipd_incumplimientos_hallazgos` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_eipd` |
| **Dado** el asistente en el paso 7 con residual alto, **entonces** «Cerrar» está deshabilitado hasta elegir una decisión. | `frontend/tests/eipd/asistente.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/MTGE-03.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 3 («Matriz de riesgos y EIPD guiada»); `INV_LOPDP_MTGE_DETERMINISTIC_TRIGGER`; metodología SPDP (*).
