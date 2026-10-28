# INC-02 · Asistente de vulneración en ocho secciones con decisión de notificar e informes de la norma técnica
`¤sdd` `¤incidentes` `¤hallazgos`

## 1. Datos

Migración `20261104_incidentes_asistente`: amplía la tabla de incidentes de INC-01 con `seccion_actual SMALLINT`, `tipo VARCHAR(16) CHECK (tipo IN ('confidencialidad','integridad','disponibilidad'))`, `decision VARCHAR(16) NULL CHECK (decision IN ('spdp','titulares','ambos','ninguno'))`, `justificacion TEXT NULL`, `informe_spdp_sha256`, `informe_titulares_sha256`, `notificado_en TIMESTAMPTZ NULL`; tabla hija `incidentes_tratamientos (tenant_id, incidente_id, tratamiento_id)` y `incidentes_lecciones (id, tenant_id, incidente_id, texto, hallazgo_id)`. RLS ENABLE y FORCE.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET /incidentes/{id}/asistente` | `implementador`, `coordinador`, `dpo`, `admin_organizacion` | — | `200 {seccion_actual, secciones: [{id, completa}]}` |
| `PUT /incidentes/{id}/asistente/{seccion}` | `implementador`, `coordinador`, `dpo` (solo secciones 7 y 8) | cuerpo de la sección | `200` |
| `POST /incidentes/{id}/informes` | `dpo`, `implementador` | `{"destino": "spdp"\|"titulares"}` | `201 {sha256, url}` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 422 | `DECISION_SIN_JUSTIFICACION` | sección 7 con `decision ≠ ninguno` y `justificacion` < 20 caracteres |
| 409 | `SECCION_ANTERIOR_INCOMPLETA` | informes antes de completar 1–6 |

## 3. Reglas

- **R1 · Orden.** Secciones 1–6 obligatorias antes de la 7; la 8 exige informes generados.
- **R2 · Decisión.** `decision ≠ 'ninguno' ⇒ len(trim(justificacion)) ≥ 20`; `decision = 'ninguno'` también exige justificación.
- **R3 · Informe.** Contenido mínimo según LEG-02: naturaleza de la vulneración, categorías y número aproximado de titulares y registros, medidas, contacto del DPO; se genera desde los datos del asistente y se custodia en `evidencias`.
- **R4 · Lecciones.** Cada lección: `registrar_hallazgo(origen='incidente', origen_ref=f"{incidente_id}:leccion:{n}", severidad='media')`.
- **R5 · Plazos.** No se calcula ningún plazo; la pantalla muestra «Plazos: pendientes de verificación legal (LEG-03)».

## 4. Interfaz

Operación › Vulneraciones: lista y asistente de ocho pasos con progreso; en la sección 7, tarjetas de decisión con justificación obligatoria; en la 8, botones «Generar informe SPDP» y «Generar comunicación a titulares» y campo de fecha de notificación con adjunto.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** la sección 7 con `decision = spdp` y justificación de 10 caracteres, **entonces** 422. Mutación: aceptarla hace fallar la prueba. | `test_decision_justificada` |
| **Dado** un incidente completo, **cuando** se genera el informe SPDP, **entonces** contiene las secciones mínimas y existe como evidencia. | `test_informe_minimo` |
| **Dado** 2 lecciones, **entonces** hay 2 hallazgos `incidente`. | `test_lecciones_hallazgos` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_incidentes_asistente` |
| **Dado** el asistente, **cuando** se intenta ir a la sección 7 con la 3 vacía, **entonces** no avanza y dice qué falta. | `frontend/tests/incidentes/asistente.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/INC-02.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 2 («Vulneraciones de seguridad»); `INV_LOPDP_INCIDENT_TIMELOCK` (el reloj llega con REG-01); LEG-02.
