# FIRMA-06 · Firma con ANF STB v2 en ambiente TEST
`¤sdd` `¤firma-electronica` `¤seguridad`

## 1. Datos

Sin migración nueva. Reutiliza `firma_sessions` (FIRMA-03), cuyas columnas `estado` y `metadatos` ya admite `lopdp_app`.

| Clave en `metadatos` | Cuándo | Contenido |
| :--- | :--- | :--- |
| `anf_solicitud_id` | Tras `POST /signs` | Id de la petición en ANF |
| `anf_ambiente` | Tras `POST /signs` | Siempre `TEST` |
| `anf_error` | Tras un rechazo definitivo | Solo el `typeCode` de ANF |

`certificado_json` de una sesión firmada declara `ambiente`, `emisor`, `anf_solicitud_id`, `timestamp_tsa_fuente = recepcion_plataforma` y `certificado_verificado = false`.

Variables de entorno, todas opcionales:

| Variable | Uso |
| :--- | :--- |
| `ANF_STB_URL` | URL base https del ambiente TEST |
| `ANF_API_ID`, `ANF_API_PASSWORD` | Generan el JWT con `POST /auth`; es la vía recomendada |
| `ANF_API_TOKEN` | JWT ya emitido; solo se usa si faltan las dos anteriores y caduca a los 10 minutos |

En el repositorio estos valores son atributos de `app_core.config.config` (`config.anf_stb_url`, `config.anf_api_token`, …), no de un objeto `settings`.

## 2. API

El contrato de ANF es el de su ficha técnica TEST (Swagger del WS 1) y es asíncrono: `POST /signs` devuelve un id, y `GET /signs/{id}/get-signed-documents` devuelve un arreglo con el PDF en Base64, un texto mientras firma, o un error `400`/`409` con `typeCode`.

| Método y ruta | Roles / Auth | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `POST /firma/sesiones/{firma_id}/anf/enviar` | tenant autenticado | `{documento_base64, paginas?}` | `202` `FirmaSession` serializada en `pendiente_firma` |
| `POST /firma/sesiones/{firma_id}/anf/sincronizar` | tenant autenticado | — | `202 {firma_id, estado}` si ANF sigue; `200 {firma_id, estado, sha256_firmado, documento_firmado_base64}` si firmó; `200 {firma_id, estado, anf_error}` si rechazó |

`paginas` usa el formato de ANF `#(x, y)`, con `#` = `primera`, `ultima` o un número; por defecto `["ultima(50, 50)"]`.

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| `404` | `FIRMA_SESION_NO_ENCONTRADA` | La sesión no existe o es de otra organización |
| `409` | `FIRMA_PROVEEDOR_INVALIDO` | La sesión no es `proveedor = anf` y `formato = pdf` |
| `409` | `FIRMA_ESTADO_INVALIDO` | `enviar` fuera de `borrador`; `sincronizar` fuera de `pendiente_firma` o sin solicitud |
| `422` | `FIRMA_DOCUMENTO_INVALIDO` | No es un PDF en Base64 o no coincide con `sha256_original` |
| `422` | `ANF_RECHAZO` | ANF rechazó el envío; `action_required` lleva su `typeCode` |
| `502` | `ANF_NO_DISPONIBLE` | Red caída, respuesta inválida o error no documentado de ANF |
| `503` | `ANF_NO_CONFIGURADO` | Sin configuración válida, o despliegue de producción |

## 3. Reglas

- **R1 · Solo TEST.** `testigos.entorno = DEV` es constante. `esta_configurado() = (APP_ENV ∉ {production, prod, produccion}) ∧ (ANF_STB_URL es https) ∧ (hay credenciales)`. Si es falso no sale ninguna petición.
- **R2 · Fallback acotado.** `firmar_documento_anf_stb` usa `boceto_firmar_documento_anf` si y solo si `¬esta_configurado() ∧ APP_ENV = test`. En otro caso, sin configuración, lanza `AnfStbNoConfiguradoError`.
- **R3 · La API nunca usa el boceto.** Una firma simulada no puede escribirse en `firma_sessions`.
- **R4 · Integridad de entrada.** Solo se envía a ANF un PDF con `sha256(pdf) = sha256_original`.
- **R5 · Una sola petición por sesión.** `enviar` reserva la fila (`borrador → pendiente_firma`) antes de llamar a ANF, en la misma transacción. Si ANF falla, la transacción revierte a `borrador`.
- **R6 · Rechazo frente a fallo transitorio.** Solo un `400`/`409` de `/signs` es definitivo. Un error de `/auth`, de red o `5xx` nunca cierra la sesión.
- **R7 · Honestidad probatoria.** ANF solo devuelve el PDF. `timestamp_tsa` guarda la hora de recepción y el certificado no se presenta como verificado hasta extraerlos del PDF.
- **R8 · Espera.** `firmar_documento_anf_stb` consulta a los 30, 60 y 90 s, como pide ANF; agotadas las esperas lanza `FirmaAnfEnProcesoError` con el id, que sigue siendo consultable.
- **R9 · Sin secretos ni datos personales en trazas.** Logs y auditoría solo llevan `typeCode` e ids; `errores[].descripcion` de ANF no se guarda.

## 4. Interfaz

Sin interfaz. El router se autoregistra con `AUTO_REGISTRO = True`.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un documento válido, **cuando** se solicita la firma, **entonces** `/auth` y `/signs` cumplen el contrato de ANF con `entorno = DEV`. | `test_solicitud_cumple_el_contrato_de_anf` |
| **Dado** solo `ANF_API_TOKEN`, **cuando** se solicita, **entonces** no se llama a `/auth`. | `test_token_fijo_sin_login` |
| **Dado** que ANF tarda, **cuando** se firma, **entonces** se consulta hasta tener el PDF y el resultado no se declara verificado. | `test_firmar_documento_anf_stb_consulta_hasta_terminar` |
| **Dado** que ANF no termina, **cuando** se agotan las esperas, **entonces** se lanza `FirmaAnfEnProcesoError` con el id. | `test_firmar_sigue_en_proceso_tras_las_esperas` |
| **Dado** un error de ANF, **cuando** responde, **entonces** solo 400 y 409 son definitivos. | `test_errores_de_anf`, `test_red_caida_no_es_rechazo`, `test_400_de_auth_no_es_rechazo_de_la_firma` |
| **Dado** un 200 sin PDF válido, **cuando** se consulta, **entonces** no se acepta. | `test_respuesta_que_no_es_pdf_se_rechaza` |
| **Dado** un ambiente sin configuración, **cuando** se firma, **entonces** el boceto responde solo con `APP_ENV=test`. | `test_boceto_solo_como_fallback_en_app_env_test` |
| **Dado** producción o una configuración insegura, **cuando** se firma, **entonces** falla sin tocar la red. | `test_falla_cerrado_sin_llamar_a_anf` |
| **Dado** una sesión en borrador, **cuando** se envía, **entonces** queda `pendiente_firma` con auditoría. | `test_enviar_deja_pendiente_y_guarda_la_solicitud` |
| **Dado** el ciclo completo, **cuando** ANF termina, **entonces** la sesión queda `firmado` con el hash del PDF recibido. | `test_ciclo_completo_firma_la_sesion` |
| **Dado** un doble envío, secuencial o simultáneo, **cuando** se procesa, **entonces** ANF recibe una sola petición. | `test_doble_envio_no_paga_dos_veces`, `test_envios_simultaneos_llaman_a_anf_una_sola_vez` |
| **Dado** un rechazo al enviar, **cuando** ANF responde, **entonces** la sesión vuelve a `borrador` y admite reintento. | `test_rechazo_de_anf_revierte_a_borrador` |
| **Dado** un error definitivo al consultar, **cuando** se sincroniza, **entonces** queda `rechazado`. | `test_error_definitivo_al_consultar_cierra_como_rechazado` |
| **Dado** ANF caído, **cuando** se sincroniza, **entonces** `502` y la sesión sigue pendiente. | `test_anf_caido_deja_la_sesion_pendiente` |
| **Dado** una sesión de A, **cuando** opera B, **entonces** `404` y ninguna llamada a ANF. | `test_aislamiento_entre_organizaciones` |
| **Dado** un documento alterado, **cuando** se envía, **entonces** `422` sin llamar a ANF. | `test_documento_invalido_no_sale_a_la_red` |
| **Dado** `APP_ENV=test` sin configuración, **cuando** se usa la API, **entonces** `503`: el boceto no llega a la base. | `test_api_nunca_usa_el_boceto` |
| **Dado** credenciales TEST reales, **cuando** se firma, **entonces** ANF devuelve un PDF. | `test_ciclo_real_contra_anf_test` |

## 6. Trazabilidad

- Ficha: `governance/tareas/FIRMA-06.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Depende de FIRMA-04 (router y serialización), FIRMA-03 (`firma_sessions`, `marcar_firmado`), RM-00 (`AUTO_REGISTRO`) y SEC-05 (`get_current_tenant`). PRD Biblioteca G («Firmas»); Aporte 111.
- Fuentes: informe de ANF «V1. Informe de entrega de STBS - SmartCidi» (15-oct-2026) y su ficha técnica TEST, leída el 2026-11-01.
- **Decisión tomada · Sin webhook.** La ficha técnica de ANF no define avisos salientes. Si ANF los ofreciera, se reutilizaría `POST /firma/webhook`.
- **Decisión tomada · Credenciales.** ANF autentica con id y contraseña y su JWT dura 10 minutos, así que `ANF_API_TOKEN` por sí solo no sirve para operar; se añadieron `ANF_API_ID` y `ANF_API_PASSWORD`.
- **Decisión abierta 1 · Verificación real.** `test_ciclo_real_contra_anf_test` no se ha ejecutado: las credenciales TEST las recibió Aleczandra Villavicencio por WhatsApp y no están en el entorno. La cabecera `Authorization` sin `Bearer` sale del ejemplo de la ficha técnica y queda por confirmar.
- **Decisión abierta 2 · Custodia.** El PDF firmado se devuelve en la respuesta de `sincronizar` y no se guarda; custodiarlo en R2 es trabajo pendiente antes de producción.
- **Decisión abierta 3 · Sello y certificado.** Extraer del PDF firmado el sello de tiempo y el certificado para sustituir los valores de R7.
- **Decisión abierta 4 · Firma del titular.** Solo se cubre el firmante precargado (`certificadoEs = false`). `firmaTitular` exige titular, adjuntos y validación biométrica u OTP reales, propios de producción.
