# DER-01 · Solicitudes de titulares: verificación de identidad, modelos de respuesta y la respuesta como evidencia
`¤sdd` `¤evidencias` `¤rbac-tenant`

## 1. Datos

Migración `20261104_derechos_respuestas`: en `derechos_arco_solicitudes` columnas `identidad_verificada_en TIMESTAMPTZ NULL`, `identidad_metodo VARCHAR(16) NULL CHECK (identidad_metodo IN ('documento','correo','presencial'))`, `identidad_verificada_por VARCHAR NULL`, `resultado VARCHAR(10) NULL CHECK (resultado IN ('concedido','denegado','parcial'))`, `respondida_en TIMESTAMPTZ NULL`. No se crea columna para el hash: se reutiliza la existente `evidencia_respuesta_hash VARCHAR(64) NULL`, que sigue admitiendo nulo porque una solicitud sin contestar no tiene evidencia. Restricción `ck_arco_contestada_con_evidencia CHECK (estado <> 'CONTESTADA' OR (evidencia_respuesta_hash ~ '^[0-9a-f]{64}$' AND respondida_en IS NOT NULL))` (`INV_ARCO_EVIDENCIA_E1`); tabla `derechos_modelos (id, tenant_id, derecho VARCHAR(32), resultado, texto TEXT, version INTEGER)`. RLS ENABLE y FORCE.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `POST /derechos/solicitudes/{id}/verificar-identidad` | `coordinador`, `responsable_area`, `admin_organizacion`, `implementador` | `{metodo}` | `200 Solicitud` |
| `GET /derechos/modelos?derecho=&resultado=` | lectura | — | `200 {modelos: [...]}` |
| `POST /derechos/solicitudes/{id}/respuesta` | `admin_organizacion`, `implementador` | `{modelo_id, variables: {…}, resultado}`, con `extra="forbid"`: el cliente no envía hash, URL ni identificador de evidencia | `201 {evidencia_respuesta_hash}` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 409 | `IDENTIDAD_NO_VERIFICADA` | responder sin verificación |
| 409 | `SOLICITUD_RESPONDIDA` | segunda respuesta |
| 422 | `VARIABLES_INCOMPLETAS` | el modelo tiene variables sin valor |
| 422 | `RESPUESTA_SIN_EVIDENCIA` | la custodia en `evidencias` no devolvió un sha256; la solicitud no cambia de estado (falla cerrada, una sola transacción) |
| 422 | (validación) | el cuerpo trae un campo no declarado, por ejemplo un hash o una URL de evidencia |

## 3. Reglas

- **R1 · Verificación previa.** `responder ⇒ identidad_verificada_en IS NOT NULL`.
- **R2 · Una respuesta.** `respondida_en IS NULL` antes de responder; después, inmutable.
- **R3 · Evidencia.** El texto resuelto se custodia en `evidencias` (tipo `respuesta_derecho`, visibilidad `organizacion`) y `evidencia_respuesta_hash` guarda el sha256 que calcula el servidor. Responder es la única vía que pasa la solicitud a `CONTESTADA`, y lo hace en la misma transacción que la custodia.
- **R3a · Sin contestar sin evidencia (`INV_ARCO_EVIDENCIA_E1`).** `estado = CONTESTADA ⇒ evidencia_respuesta_hash ~ ^[0-9a-f]{64}$ ∧ respondida_en IS NOT NULL`. Lo exigen el servicio (422 `RESPUESTA_SIN_EVIDENCIA`) y la base (`ck_arco_contestada_con_evidencia`), para que una ruta futura o un UPDATE directo tampoco puedan saltárselo.
- **R3b · Hash del servidor.** El hash nunca viene del cliente. El tipo `ResolverSolicitudArcoInput` (`frontend/src/types/arco.ts`, con `evidenciaUrl`) se retira; `frontend/src/lib/derechos/respuestas.ts` envía solo `{modelo_id, variables, resultado}`.
- **R4 · Sin plazo.** Ninguna fecha de vencimiento se calcula aquí.
- **R-ADPA · Ortogonalidad ZERAG (`DER-01`).** Toda invocación a otra sala se realiza vía `app_core/pasillo/<otra_sala>.py#DER-01` (`ImportsCruzados = ∅`, ADR 0001) y los códigos de `ErrorNegocio` (`app_core.errors`) se registran en `features/<sala>/domain/errores.py#DER-01`.

## 4. Interfaz

Operación › Solicitudes de titulares: ficha con bloque «Identidad» (método y botón «Verificar»), bloque «Respuesta» con selector de modelo, variables y vista previa; «Enviar» solo para quien aprueba; estado «Respondida» con enlace a la evidencia.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una solicitud sin verificar, **cuando** se responde, **entonces** 409 `IDENTIDAD_NO_VERIFICADA`. Mutación: omitir la comprobación hace fallar la prueba. | `test_responder_exige_identidad` |
| **Dado** una solicitud verificada, **cuando** el `implementador` responde con un modelo, **entonces** existe la evidencia, `evidencia_respuesta_hash` coincide con su sha256 y el estado es `CONTESTADA`. | `test_respuesta_como_evidencia` |
| **Dado** una solicitud verificada y una custodia que falla, **cuando** se responde, **entonces** 422 `RESPUESTA_SIN_EVIDENCIA` y el estado no cambia. Mutación: quitar la comprobación del servicio hace fallar la prueba. | `test_contestar_sin_evidencia_422` |
| **Dado** un cuerpo con `evidencia_respuesta_hash` o `evidenciaUrl`, **cuando** se responde, **entonces** 422 y no se guarda nada. Mutación: aceptar el hash del cliente hace fallar la prueba (manda un hash que no corresponde a ninguna evidencia). | `test_hash_del_cliente_rechazado` |
| **Dado** una solicitud sin evidencia, **cuando** un UPDATE directo con `lopdp_app` la pasa a `CONTESTADA`, **entonces** la base lo rechaza. Mutación: quitar `ck_arco_contestada_con_evidencia` de la migración hace fallar la prueba. | `test_check_contestada_exige_hash` |
| **Dado** un `dpo`, **cuando** responde, **entonces** 403. | `test_dpo_no_responde_derechos` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_derechos_respuestas` |
| **Dado** la ficha, **cuando** se elige un modelo con una variable vacía, **entonces** «Enviar» queda deshabilitado. | `frontend/tests/derechos/respuestas.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/DER-01.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 2 («Derechos de los titulares»); `INV_ARCO_EVIDENCIA_E1` (PR #657); decisión 1 (el DPO no ejecuta); los plazos, REG-01 y LEG-03.
