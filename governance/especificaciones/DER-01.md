# DER-01 · Solicitudes de titulares: verificación de identidad, modelos de respuesta y la respuesta como evidencia
`¤sdd` `¤evidencias` `¤rbac-tenant`

## 1. Datos

Migración `20261104_derechos_respuestas`: en `derechos_arco_solicitudes` columnas `identidad_verificada_en TIMESTAMPTZ NULL`, `identidad_metodo VARCHAR(16) NULL CHECK (identidad_metodo IN ('documento','correo','presencial'))`, `identidad_verificada_por VARCHAR NULL`, `resultado VARCHAR(10) NULL CHECK (resultado IN ('concedido','denegado','parcial'))`, `respuesta_sha256 VARCHAR(64) NULL`, `respondida_en TIMESTAMPTZ NULL`; tabla `derechos_modelos (id, tenant_id, derecho VARCHAR(32), resultado, texto TEXT, version INTEGER)`. RLS ENABLE y FORCE.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `POST /derechos/solicitudes/{id}/verificar-identidad` | `coordinador`, `responsable_area`, `admin_organizacion`, `implementador` | `{metodo}` | `200 Solicitud` |
| `GET /derechos/modelos?derecho=&resultado=` | lectura | — | `200 {modelos: [...]}` |
| `POST /derechos/solicitudes/{id}/respuesta` | `admin_organizacion`, `implementador` | `{modelo_id, variables: {…}, resultado}` | `201 {respuesta_sha256}` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 409 | `IDENTIDAD_NO_VERIFICADA` | responder sin verificación |
| 409 | `SOLICITUD_RESPONDIDA` | segunda respuesta |
| 422 | `VARIABLES_INCOMPLETAS` | el modelo tiene variables sin valor |

## 3. Reglas

- **R1 · Verificación previa.** `responder ⇒ identidad_verificada_en IS NOT NULL`.
- **R2 · Una respuesta.** `respondida_en IS NULL` antes de responder; después, inmutable.
- **R3 · Evidencia.** El texto resuelto se custodia en `evidencias` (tipo `respuesta_derecho`, visibilidad `organizacion`) y `respuesta_sha256` lo referencia.
- **R4 · Sin plazo.** Ninguna fecha de vencimiento se calcula aquí.

## 4. Interfaz

Operación › Solicitudes de titulares: ficha con bloque «Identidad» (método y botón «Verificar»), bloque «Respuesta» con selector de modelo, variables y vista previa; «Enviar» solo para quien aprueba; estado «Respondida» con enlace a la evidencia.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una solicitud sin verificar, **cuando** se responde, **entonces** 409 `IDENTIDAD_NO_VERIFICADA`. Mutación: omitir la comprobación hace fallar la prueba. | `test_responder_exige_identidad` |
| **Dado** una solicitud verificada, **cuando** el `implementador` responde con un modelo, **entonces** existe la evidencia y `respuesta_sha256` coincide. | `test_respuesta_como_evidencia` |
| **Dado** un `dpo`, **cuando** responde, **entonces** 403. | `test_dpo_no_responde_derechos` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_derechos_respuestas` |
| **Dado** la ficha, **cuando** se elige un modelo con una variable vacía, **entonces** «Enviar» queda deshabilitado. | `frontend/tests/derechos/respuestas.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/DER-01.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 2 («Derechos de los titulares»); decisión 1 (el DPO no ejecuta); los plazos, REG-01 y LEG-03.
