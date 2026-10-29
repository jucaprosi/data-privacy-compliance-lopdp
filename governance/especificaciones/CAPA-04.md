# CAPA-04 · Auditoría con grilla de verificación por dominio y acta por área, con hallazgos al plan de acción
`¤sdd` `¤auditoria-capa` `¤hallazgos`

## 1. Datos

Migración `20261106_auditoria_grilla`: `auditorias (id, tenant_id, nombre, alcance JSONB, equipo JSONB, estado VARCHAR(10) CHECK (IN ('abierta','cerrada')), creado_por, creado_en, cerrada_en)`, `auditoria_filas (id, tenant_id, auditoria_id, control_ref, declarado SMALLINT, riesgo_inicial SMALLINT, verificado SMALLINT NULL, evidencia_sha256 NULL, riesgo_final SMALLINT NULL, revisado_por NULL, hallazgo_id NULL, UNIQUE (auditoria_id, control_ref))`, `auditoria_actas (id, tenant_id, auditoria_id, area_id, texto, acta_sha256)`. RLS ENABLE y FORCE.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `POST /auditoria-capa/auditorias` | `implementador`, `coordinador` | `{nombre, alcance, equipo}` | `201` con filas precargadas desde el último resultado sellado |
| `PUT /auditoria-capa/auditorias/{id}/filas/{control_ref}` | miembro del equipo auditor | `{verificado, evidencia_sha256?, riesgo_final}` | `200` |
| `POST /auditoria-capa/auditorias/{id}/cerrar` | `implementador` | — | `200 {actas: [{area_id, acta_sha256}]}` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 403 | `AUDITOR_EJECUTOR` | el revisor ejecutó tareas de ese control (responsable de tareas con ese `control_ref`) |
| 409 | `AUDITORIA_INCOMPLETA` | cerrar con filas sin `verificado` |
| 404 | `DIAG_SIN_RESULTADO` | crear sin resultado sellado |

## 3. Reglas

- **R1 · Precarga.** `declarado = nivel_sellado` del último resultado por control; `riesgo_inicial = (5 − declarado) × criticidad` (misma fórmula del diagnóstico).
- **R2 · Hallazgo.** `verificado < declarado ⇒ registrar_hallazgo(origen='auditoria', origen_ref=f"{auditoria_id}:{control_ref}", severidad = 'critica' si riesgo_final ≥ 15, 'alta' si ≥ 9, 'media')`.
- **R3 · SoD.** `revisado_por ∉ {owner de tareas con ese control_ref}`.
- **R4 · Acta.** Una por área del alcance, texto fijo con alcance, filas del área y evidencias; custodiada en `evidencias` (tipo `acta_auditoria`); prohibida la palabra «certificado» (prueba).

## 4. Interfaz

Riesgos y auditoría › Auditorías: lista; grilla editable por el equipo con evidencia por fila; cierre con actas descargables por área.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una fila con declarado 3 y verificado 1, **entonces** se crea un hallazgo `auditoria`. | `test_grilla_genera_hallazgo` |
| **Dado** un revisor que es responsable de una tarea de P12, **cuando** verifica P12, **entonces** 403 `AUDITOR_EJECUTOR`. Mutación: permitirlo hace fallar la prueba. | `test_auditor_no_ejecutor` |
| **Dado** el cierre, **entonces** hay un acta por área del alcance, custodiada, y ninguna contiene «certificado». | `test_actas_por_area` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_auditorias` |
| **Dado** la grilla, **cuando** se completa la última fila, **entonces** «Cerrar» se habilita. | `frontend/tests/auditoria/grilla.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/CAPA-04.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 3 («Grilla de verificación», «acta de auditoría por área»); Doctrina 1; D-4.
