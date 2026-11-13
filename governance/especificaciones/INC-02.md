# INC-02 · Asistente de vulneración en ocho secciones con decisión de notificar e informes de la norma técnica
`¤sdd` `¤incidentes` `¤hallazgos`

## 1. Datos

Enmienda del Arquitecto ADPA (2026-11-13). **La tabla `incidentes` no se toca.** INC-01 la define inmutable y `lopdp_app` solo tiene `SELECT, INSERT` sobre ella (`20261028_bitacora_incidentes.py`). Guardar una sección del asistente sobre esa tabla exigiría `UPDATE`. El asistente vive en tablas propias que solo se agregan, con el patrón de `incidentes_eventos_estado` (INC-03).

Migración `inc02_incidentes_asistente.py`, sin fecha; `down_revision` = la cabeza de `main` al implementar (FUSION_ALEMBIC).

- `incidentes_asistente_secciones (id, tenant_id, incidente_id, seccion SMALLINT CHECK (seccion BETWEEN 1 AND 8), version INTEGER, datos JSONB, registrado_por, registrado_en, UNIQUE (incidente_id, seccion, version))`.
  - Cada guardado es una versión nueva; vale la de mayor `version` por sección.
  - En la sección 4, CHECK de `datos->>'tipo'` IN (`confidencialidad`, `integridad`, `disponibilidad`).
  - En la sección 7, CHECK de `datos->>'decision'` IN (`spdp`, `titulares`, `ambos`, `ninguno`) y de `length(trim(datos->>'justificacion')) >= 20`.
- `incidentes_informes (id, tenant_id, incidente_id, destino VARCHAR(10) CHECK (destino IN ('spdp','titulares')), sha256, evidencia_id, emitido_por, emitido_en)`.
- `incidentes_notificaciones (id, tenant_id, incidente_id, destino VARCHAR(10) CHECK (destino IN ('spdp','titulares')), notificado_en TIMESTAMPTZ, evidencia_sha256, registrado_por, registrado_en)`.
- `incidentes_tratamientos (id, tenant_id, incidente_id, tratamiento_id, registrado_por, registrado_en)`.
- `incidentes_lecciones (id, tenant_id, incidente_id, numero INTEGER, texto, hallazgo_id, registrado_por, registrado_en, UNIQUE (incidente_id, numero))`.
- FK compuesta `(incidente_id, tenant_id)` → `incidentes(id, tenant_id)` en las cinco tablas, sobre `uq_incidentes_id_tenant` de INC-03.
- RLS `ENABLE` y `FORCE` con `USING` y `WITH CHECK` por `tenant_id`. `lopdp_app` con `SELECT, INSERT` en las cinco, sin `UPDATE` ni `DELETE`.
- `seccion_actual` no se guarda: es la primera sección sin versión completa.
- La decisión de notificar vigente es la de la última versión de la sección 7. Quién decidió y cuándo son `registrado_por` y `registrado_en` de esa fila.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET /incidentes/{id}/asistente` | `implementador`, `coordinador`, `dpo`, `admin_organizacion` | — | `200 {seccion_actual, secciones: [{id, completa}]}` |
| `PUT /incidentes/{id}/asistente/{seccion}` | `implementador`, `coordinador`, `dpo` (solo secciones 7 y 8) | cuerpo de la sección | `200` |
| `POST /incidentes/{id}/informes` | `dpo`, `implementador` | `{"destino": "spdp"\|"titulares"}` | `201 {sha256, evidencia_id}` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 422 | `DECISION_SIN_JUSTIFICACION` | sección 7 con `decision ≠ ninguno` y `justificacion` < 20 caracteres |
| 409 | `SECCION_ANTERIOR_INCOMPLETA` | sección 7 o informes antes de completar 1–6; sección 8 sin informes |
| 409 | `DECISION_NOTIFICAR_PENDIENTE` | cerrar (INC-03) un incidente con `afecta_datos_personales` sin versión de la sección 7 |

## 3. Reglas

- **R1 · Orden.** Secciones 1–6 obligatorias antes de la 7; la 8 exige informes generados.
- **R2 · Decisión.** `decision ≠ 'ninguno' ⇒ len(trim(justificacion)) ≥ 20`; `decision = 'ninguno'` también exige justificación.
- **R3 · Informe.** Contenido mínimo según LEG-02: naturaleza de la vulneración, categorías y número aproximado de titulares y registros, medidas, contacto del DPO; se genera desde la última versión de cada sección y se custodia por `custodiar_documento_generado` de la compuerta de evidencias (EVI-04), con tipo `informe_incidente`. No se registra una huella sin el documento. Regenerar un informe agrega otra fila; no reemplaza la anterior.
- **R4 · Lecciones.** Cada lección: `registrar_hallazgo(origen='incidente', origen_ref=f"{incidente_id}:leccion:{n}", severidad='media')`.
- **R6 · Solo se agrega.** Ninguna operación del asistente hace `UPDATE` ni `DELETE`. Corregir una sección es guardar otra versión, y la anterior queda como rastro.
- **R7 · Precondición de cierre.** El cierre de INC-03 de un incidente con `afecta_datos_personales` exige una versión de la sección 7; si no, 409 `DECISION_NOTIFICAR_PENDIENTE`. La comprobación vive en la sección `INC-02` de `incidentes_service.py` y `cerrar_incidente` la llama.
- **R5 · Plazos.** No se calcula ningún plazo; la pantalla muestra «Plazos: pendientes de verificación legal (LEG-03)».
- **R-ADPA · Ortogonalidad ZERAG (`INC-02`).** Toda invocación a otra sala se realiza vía `app_core/pasillo/<otra_sala>.py#INC-02` (`ImportsCruzados = ∅`, ADR 0001) y los códigos de `ErrorNegocio` (`app_core.errors`) se registran en `features/<sala>/domain/errores.py#INC-02`.

## 4. Interfaz

Operación › Vulneraciones: lista y asistente de ocho pasos con progreso; en la sección 7, tarjetas de decisión con justificación obligatoria; en la 8, botones «Generar informe SPDP» y «Generar comunicación a titulares» y campo de fecha de notificación con adjunto.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** la sección 7 con `decision = spdp` y justificación de 10 caracteres, **entonces** 422. Mutación: aceptarla hace fallar la prueba. | `test_decision_justificada` |
| **Dado** un incidente completo, **cuando** se genera el informe SPDP, **entonces** contiene las secciones mínimas y existe como evidencia. | `test_informe_minimo` |
| **Dado** 2 lecciones, **entonces** hay 2 hallazgos `incidente`. | `test_lecciones_hallazgos` |
| **Dado** la sección 3 guardada dos veces, **entonces** hay dos versiones y el `GET` devuelve la última. Con `lopdp_app`, `UPDATE` y `DELETE` sobre las cinco tablas y `UPDATE` sobre `incidentes` dan permiso denegado. Mutación: conceder `UPDATE` hace fallar la prueba. | `test_asistente_solo_agrega` |
| **Dado** un incidente con datos personales sin sección 7, **cuando** se cierra por `POST /incidentes/{id}/cerrar`, **entonces** 409 `DECISION_NOTIFICAR_PENDIENTE`; con la sección 7 guardada, cierra. Mutación: quitar la llamada a la precondición. | `test_cierre_exige_decision` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_incidentes_asistente` |
| **Dado** el asistente, **cuando** se intenta ir a la sección 7 con la 3 vacía, **entonces** no avanza y dice qué falta. | `frontend/tests/incidentes/asistente.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/INC-02.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 2 («Vulneraciones de seguridad»); `INV_LOPDP_INCIDENT_TIMELOCK` (el reloj llega con REG-01); LEG-02.
