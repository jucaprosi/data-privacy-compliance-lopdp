# DER-01 · Solicitudes de titulares: verificación de identidad, modelos de respuesta y la respuesta como evidencia
`¤sdd` `¤evidencias` `¤rbac-tenant`

## 1. Datos

Migración nueva `alembic/versions/der01_derechos_respuestas.py`. El nombre no lleva fecha, como `bib301_biblioteca_aprobaciones.py`, para que la propiedad de la ficha no cambie. Su `down_revision` es la cabeza de `main` al implementar (hoy `20261123_der06a_tipos_solicitud`; después de ORG-22a, la que haya) y al fusionar queda una sola cabeza (FUSION_ALEMBIC). En `derechos_arco_solicitudes` columnas `identidad_verificada_en TIMESTAMPTZ NULL`, `identidad_metodo VARCHAR(16) NULL CHECK (identidad_metodo IN ('documento','correo','presencial'))`, `identidad_verificada_por VARCHAR NULL`, `resultado VARCHAR(10) NULL CHECK (resultado IN ('concedido','denegado','parcial'))`, `respondida_en TIMESTAMPTZ NULL`. No se crea columna para el hash: se reutiliza la existente `evidencia_respuesta_hash VARCHAR(64) NULL`, que sigue admitiendo nulo porque una solicitud sin contestar no tiene evidencia. Restricción `ck_arco_contestada_con_evidencia CHECK (estado <> 'CONTESTADA' OR (evidencia_respuesta_hash ~ '^[0-9a-f]{64}$' AND respondida_en IS NOT NULL))` (`INV_ARCO_EVIDENCIA_E1`). **Datos existentes:** antes del `ADD CONSTRAINT`, la migración cuenta las filas con `estado = 'CONTESTADA'` y sin hash válido. Si hay alguna, aborta con un mensaje que da el recuento, sin `UPDATE` silencioso: la corrección de esas filas (demo o producción) la decide el propietario. Tabla `derechos_modelos (id, tenant_id, derecho VARCHAR(32), resultado, texto TEXT, version INTEGER)`. RLS ENABLE y FORCE. La migración siembra los modelos de §4.1.

**Resultado de la queja.** `resultado` guarda el desenlace de la petición frente a lo pedido: `concedido` (se atiende entera), `parcial` (se atiende en parte) y `denegado` (no se atiende). Una queja al responsable tiene exactamente esos tres desenlaces, así que reutiliza los tres valores y el CHECK queda en `('concedido','denegado','parcial')`. Cambia solo la etiqueta que ve la persona (§4.1). `resultado` es una columna nueva de esta migración: no hay filas previas que contar.

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

Operación › Solicitudes de titulares: ficha con bloque «Identidad» (método y botón «Verificar»), bloque «Respuesta» con selector de modelo, variables y vista previa, y el botón «Registrar la respuesta» solo para quien aprueba. Bajo el botón va la línea fija «La respuesta queda registrada como evidencia. Entrégala al titular por el medio que indicó en su solicitud.» y el enlace «Descargar la respuesta». La plataforma no envía nada al titular. El estado «Respondida» lleva el enlace a la evidencia. Los demás textos de pantalla son los de la ficha, cerrados por UX/UI.

### 4.1 Modelos de respuesta

Son datos: los siembra la migración en `derechos_modelos` y la prueba los lee de aquí. Cada modelo es encabezado + cuerpo por resultado + cierre + firma, en texto plano.

**Variables.** Comunes y obligatorias: `{organizacion}`, `{nombre_titular}`, `{fecha_solicitud}`, `{numero_solicitud}`, `{fecha_respuesta}`, `{contacto_dpo}`. Por resultado: `concedido` → `{actuacion}`; `parcial` → `{actuacion}` y `{motivo}`; `denegado` → `{motivo}`. `{motivo}` es texto libre de la organización; el modelo no añade base legal.

**Encabezado.** «{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.», salto de línea, «Estimado/a {nombre_titular}:».

**Cuerpos.** Para cada derecho, con su objeto `<objeto>`:
- `concedido`: «Atendimos tu solicitud <objeto>. {actuacion}»
- `parcial`: «Atendimos en parte tu solicitud <objeto>. {actuacion} No pudimos atender el resto por este motivo: {motivo}»
- `denegado`: «No podemos atender tu solicitud <objeto> por este motivo: {motivo}»

| `derecho` | Cita | `<objeto>` |
| :--- | :--- | :--- |
| `ACCESO` | LOPDP, art. 13 | «de acceso a tus datos personales» |
| `RECTIFICACION` | LOPDP, art. 14 | «de rectificación y actualización de tus datos personales» |
| `CANCELACION` | LOPDP, art. 15 | «de eliminación de tus datos personales» |
| `OPOSICION` | LOPDP, art. 16 | «de oposición al tratamiento de tus datos personales» |
| `PORTABILIDAD` | LOPDP, art. 17 | «de portabilidad de tus datos personales» |
| `SUSPENSION` | LOPDP, art. 19 | «de suspensión del tratamiento de tus datos personales» |
| `DECISIONES_AUTOMATIZADAS` | LOPDP, art. 20 | «de no ser objeto de una decisión basada en valoraciones automatizadas» |

La cita va entre paréntesis una sola vez, tras `<objeto>` en la primera frase. Las claves están en `governance/artefactos/CITAS_LEGALES_VERIFICADAS.md`.

**Queja (`QUEJA`).** Sin cita en el cuerpo. Etiquetas del resultado en pantalla: «Atendida», «Atendida en parte» y «No atendida». Cuerpos:
- `concedido`: «Revisamos tu queja. {actuacion}»
- `parcial`: «Revisamos tu queja en parte. {actuacion} Sobre el resto: {motivo}»
- `denegado`: «Revisamos tu queja y no podemos atenderla por este motivo: {motivo}»

Para los demás derechos, las etiquetas son «Concedida», «Parcial» y «Denegada». Un derecho sin fila en esta sección (por ejemplo, anulación) no tiene modelo y el selector no lo ofrece.

**Ayuda en pantalla** (no forma parte del texto). En `denegado` y `parcial` de `RECTIFICACION`, `CANCELACION`, `OPOSICION` y `PORTABILIDAD`: «Si te apoyas en una excepción de la ley, indícala en el motivo (LOPDP, art. 18).» (clave `LOPDP-art-18`).

**Cierre.** «Si tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}.» En `denegado` y `parcial`, además: «Si no estás de acuerdo con esta respuesta, puedes acudir a la Autoridad de Protección de Datos Personales.» Firma: «{organizacion} · {fecha_respuesta}».

**Contenido.** Los modelos no mencionan plazos ni el art. 62 (R4); el plazo lo muestra DER-07. No contienen «conforme a la ley», «en cumplimiento de» ni «garantizamos».

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una solicitud sin verificar, **cuando** se responde, **entonces** 409 `IDENTIDAD_NO_VERIFICADA`. Mutación: omitir la comprobación hace fallar la prueba. | `test_responder_exige_identidad` |
| **Dado** una solicitud verificada, **cuando** el `implementador` responde con un modelo, **entonces** existe la evidencia, `evidencia_respuesta_hash` coincide con su sha256 y el estado es `CONTESTADA`. | `test_respuesta_como_evidencia` |
| **Dado** una solicitud verificada y una custodia que falla, **cuando** se responde, **entonces** 422 `RESPUESTA_SIN_EVIDENCIA` y el estado no cambia. Mutación: quitar la comprobación del servicio hace fallar la prueba. | `test_contestar_sin_evidencia_422` |
| **Dado** un cuerpo con `evidencia_respuesta_hash` o `evidenciaUrl`, **cuando** se responde, **entonces** 422 y no se guarda nada. Mutación: aceptar el hash del cliente hace fallar la prueba (manda un hash que no corresponde a ninguna evidencia). | `test_hash_del_cliente_rechazado` |
| **Dado** una solicitud sin evidencia, **cuando** un UPDATE directo con `lopdp_app` la pasa a `CONTESTADA`, **entonces** la base lo rechaza. Mutación: quitar `ck_arco_contestada_con_evidencia` de la migración hace fallar la prueba. | `test_check_contestada_exige_hash` |
| **Dado** una base con una fila `CONTESTADA` sin hash, **cuando** se aplica la migración, **entonces** aborta con el recuento (1) y la fila no cambia. Mutación: reemplazar el recuento por un `UPDATE` que rellene el hash hace fallar la prueba. | `test_migracion_der01_aborta_con_contestadas_sin_hash` |
| **Dado** un `dpo`, **cuando** responde, **entonces** 403. | `test_dpo_no_responde_derechos` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_derechos_respuestas` |
| **Dado** la migración aplicada, **entonces** `derechos_modelos` tiene un modelo por cada par (derecho, resultado) de §4.1, 24 en total, y cada texto resuelto con variables de ejemplo es idéntico al de §4.1. Mutación: cambiar una frase sembrada hace fallar la prueba. | `test_modelos_sembrados_segun_especificacion` |
| **Dado** una queja verificada, **cuando** se responde con `resultado = parcial`, **entonces** la respuesta usa el cuerpo de la queja y el CHECK de `resultado` no admite otros valores. | `test_queja_reutiliza_resultados` |
| **Dado** la ficha, **cuando** se elige un modelo con una variable vacía, **entonces** «Registrar la respuesta» tiene `aria-disabled` y ningún texto visible promete un envío. | `frontend/tests/derechos/respuestas.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/DER-01.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 2 («Derechos de los titulares»); `INV_ARCO_EVIDENCIA_E1` (PR #657); decisión 1 (el DPO no ejecuta); los plazos, REG-01 y LEG-03.
