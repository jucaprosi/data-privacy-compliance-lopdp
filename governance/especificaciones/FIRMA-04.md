# FIRMA-04 · API HTTP de firma electrónica y webhook HMAC-SHA256
`¤sdd` `¤firma-electronica` `¤seguridad` `¤rbac-tenant`

## 1. Datos

Sin migración nueva. Reutiliza `firma_sessions` (FIRMA-03). La variable de entorno `FIRMA_WEBHOOK_SECRET` (string no vacío) autentica el webhook; sin ella todos los avisos se rechazan.

## 2. API

| Método y ruta | Roles / Auth | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `POST /firma/sesiones` | tenant autenticado | `{documento_id, firmante_id, formato, proveedor, sha256_original}` | `201` `FirmaSession` serializada |
| `GET /firma/sesiones/{firma_id}` | tenant autenticado | — | `200` `FirmaSession` o `404` |
| `GET /firma/sesiones?estado=` | tenant autenticado | `estado` opcional | `200 {"sesiones": [...]}` |
| `POST /firma/webhook` | HMAC-SHA256 en `X-Signature` | `{firma_id, tenant_id, sha256_firmado, timestamp_tsa, certificado_json?}` | `200 {"firma_id", "estado"}` |

**Formatos válidos:** `pdf`, `xml`, `json`. **Proveedores válidos:** `anf`, `universign`, `stub`.

| Código HTTP | Cuándo |
| :--- | :--- |
| `401` | Webhook con HMAC inválido, ausente o sin secreto configurado |
| `404` | Sesión no existe o pertenece a otro tenant |
| `409` | Webhook sobre una sesión ya cerrada (`TransicionFirmaInvalidaError`) |
| `422` | `estado` desconocido en el listado; tenant no es UUID |

## 3. Reglas

- **R1 · Identidad.** Los tres endpoints de sesiones toman el tenant del token autenticado (`get_current_tenant`); nunca del cuerpo. El webhook toma el `tenant_id` del body JSON, autorizado únicamente por el HMAC.
- **R2 · Webhook falla cerrado.** Si `FIRMA_WEBHOOK_SECRET` no está configurado o `X-Signature` está ausente, siempre `401`, sin interpretar el cuerpo ni tocar la base.
- **R3 · Comparación en tiempo constante.** La verificación HMAC usa `hmac.compare_digest`, nunca `==`.
- **R4 · BD después de la auth.** El webhook verifica el HMAC antes de parsear el JSON y antes de cualquier acceso a la base de datos.
- **R5 · Sin tabla nueva.** Todo acceso a datos pasa por la compuerta `firma_electronica_service`; no hay SQL directo en el router.
- **R6 · sha256_original normalizado.** Se almacena en minúsculas (`lower()`); el campo tiene patrón `^[0-9a-fA-F]{64}$`.

## 4. Interfaz

Sin interfaz. El router se autoregistra con `AUTO_REGISTRO = True`.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una solicitud válida, **cuando** se crea la sesión, **entonces** responde `201` con `estado = borrador`; la organización B no la ve (`404`). | `test_crear_sesion_ok` |
| **Dado** una sesión existente, **cuando** la pide su tenant, **entonces** devuelve los datos con `estado = borrador`. | `test_obtener_sesion_ok` |
| **Dado** una sesión de A, **cuando** la pide B, **entonces** `404`; el listado de B queda vacío. | `test_obtener_sesion_otro_tenant` |
| **Dado** dos sesiones, una firmada por webhook y otra en borrador, **cuando** se listan por estado, **entonces** cada filtro devuelve solo las suyas. | `test_listar_sesiones_filtro_estado` |
| **Dado** un webhook con HMAC correcto, **cuando** se procesa, **entonces** `200`, la sesión pasa a `firmado` con `sha256_firmado`, `timestamp_tsa` y `certificado_json`. | `test_webhook_hmac_valido` |
| **Dado** un webhook con HMAC de otro secreto, **cuando** se procesa, **entonces** `401 firma_invalida`; la sesión sigue en `borrador`; la comparación pasó por `compare_digest`. Mutación: sustituir `compare_digest` por `==` hace fallar la prueba. | `test_webhook_hmac_invalido` |
| **Dado** un webhook sin cabecera `X-Signature`, **cuando** se procesa, **entonces** `401 firma_invalida`; la sesión no cambia. | `test_webhook_hmac_ausente` |

## 6. Trazabilidad

- Ficha: `governance/tareas/FIRMA-04.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Depende de FIRMA-03 (tabla `firma_sessions` y motor async), RM-00 (`AUTO_REGISTRO`), SEC-05 (`get_current_tenant`).
- PRD Biblioteca G («Firmas»), §5.9; Aporte 111 (proveedores con certificado, fuera de alcance).
- **Decisión abierta 1 · Secreto del webhook.** `FIRMA_WEBHOOK_SECRET` se lee de entorno; no hay rotación automática. El propietario decide si se gestiona con un gestor de secretos o directamente en Vercel.
- **Decisión abierta 2 · tenant_id en el webhook.** El aviso del proveedor incluye `tenant_id` en el body porque el webhook no lleva identidad de usuario. Si el proveedor real no lo incluye, se necesitará un mecanismo alternativo de localización de la sesión (pendiente de evaluar con cada proveedor).
