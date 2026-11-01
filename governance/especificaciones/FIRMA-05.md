# FIRMA-05 · Matrices de aceptación deterministas de FIRMA-03 y FIRMA-04
`¤sdd` `¤firma-electronica` `¤arbitro`

## 1. Datos

Sin migración ni tabla nueva. Los dos archivos de matriz exportan `FILAS = []` porque los endpoints de firma resuelven la organización por identidad autenticada o por HMAC, no por rol; `test_matriz_permisos.py` exige la lista en cada archivo de `tests/matriz/` y acepta vacía.

## 2. API

Sin endpoint nuevo. Los casos de matriz usan la API ya definida en FIRMA-03 y FIRMA-04.

## 3. Reglas

- **R1 · FILAS vacía.** `FILAS: list[tuple[str, str, str, set[str]]] = []` en cada archivo; no se añaden filas de roles.
- **R2 · Aislamiento por UUID.** Cada caso crea sus propios tenants con `uuid4()`, no depende del orden de ejecución y limpia lo que crea en el bloque `finally`.
- **R3 · Sin producción.** El fixture afirma que `TEST_DATABASE_URL` no contiene `ep-late-hall-b50bpbk5`.
- **R4 · Rol restringido.** Los casos de FIRMA-03 usan `SET LOCAL ROLE lopdp_app` para verificar los permisos de la tabla `firma_sessions`; los de FIRMA-04 usan el router HTTP con `AsyncClient`.
- **R5 · Sin secretos en código.** El secreto del webhook en FIRMA-04.py se genera con `secrets.token_hex(16)` en cada ejecución y se inyecta con `monkeypatch.setenv`.

## 4. Interfaz

Sin interfaz.

## 5. Aceptación

Las matrices se ejecutan por ruta, contra la rama Neon de pruebas de la persona: `pytest tests/matriz/FIRMA-03.py tests/matriz/FIRMA-04.py`.

### Matriz FIRMA-03 (10 casos)

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una organización, **cuando** se crea una sesión y se relee en una sesión de BD nueva, **entonces** es la misma fila y está en `borrador` (F03-01). | `test_crear_sesion_persiste` |
| **Dado** una sesión creada, **cuando** se lee y `lopdp_app` intenta reescribir `sha256_original` o `firmante_id` o borrarla, **entonces** quedan guardados todos los campos obligatorios y la base responde `42501` sin alterar la fila (F03-02). | `test_crear_sesion_campos_completos` |
| **Dado** una sesión en `borrador`, **cuando** se llama a `marcar_firmado`, **entonces** pasa a `firmado` con `sha256_firmado`, `timestamp_tsa` y certificado, y una segunda llamada lanza `TransicionFirmaInvalidaError` (F03-03). | `test_marcar_firmado_actualiza_estado` |
| **Dado** una sesión de la organización A, **cuando** B la pide, **entonces** `obtener_sesion` devuelve `None`, y B no puede insertar una fila de A (`42501`, WITH CHECK) (F03-04). | `test_rls_tenant_a_no_ve_tenant_b` |
| **Dado** 3 sesiones de A y 2 de B, **cuando** cada una lista, **entonces** ve solo las suyas (F03-05). | `test_rls_listar_solo_propio_tenant` |
| **Dado** una sesión recién creada, **cuando** se consulta `audit_events`, **entonces** hay exactamente un evento `crear_sesion_firma` de `firma_session` (F03-06). | `test_audit_event_al_crear` |
| **Dado** una sesión creada y firmada, **cuando** se consulta `audit_events`, **entonces** están `crear_sesion_firma` y `marcar_firmado` (F03-07). | `test_audit_event_al_firmar` |
| **Dado** 2 sesiones firmadas y 1 en borrador, **cuando** se lista con `estado="firmado"`, **entonces** devuelve 2, y un estado desconocido lanza `ValueError` (F03-08). | `test_listar_filtro_estado` |
| **Dado** los bocetos de FIRMA-01, **cuando** se llama a `boceto_firmar_documento_anf`, **entonces** devuelve un `ResultadoFirma` en estado `FIRMADO` (F03-09). | `test_bocetos_compatibles` |
| **Dado** un UUID aleatorio, **cuando** se llama a `obtener_sesion`, **entonces** devuelve `None`, y `marcar_firmado` lanza `SesionFirmaNoEncontradaError` (F03-10). | `test_obtener_sesion_inexistente` |

### Matriz FIRMA-04 (11 casos)

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una solicitud válida, **cuando** se hace `POST /api/v1/firma/sesiones`, **entonces** 201 con `firma_id` UUID y estado `borrador` (F04-01). | `test_post_sesiones_crea_ok` |
| **Dado** un cuerpo incompleto o con valores fuera de contrato, **cuando** se envía, **entonces** 422 y no se escribe nada (F04-02). | `test_post_sesiones_campos_invalidos` |
| **Dado** una sesión de la organización, **cuando** se hace `GET /api/v1/firma/sesiones/{firma_id}`, **entonces** 200 con la misma sesión (F04-03). | `test_get_sesion_ok` |
| **Dado** una sesión de A, **cuando** la pide B, **entonces** 404 (F04-04). | `test_get_sesion_otro_tenant_404` |
| **Dado** un UUID aleatorio, **cuando** se pide, **entonces** 404; un id que no es UUID da 422 (F04-05). | `test_get_sesion_inexistente_404` |
| **Dado** una organización sin sesiones, **cuando** lista, **entonces** 200 con `{"sesiones": []}` aunque otra tenga (F04-06). | `test_get_sesiones_lista_vacia` |
| **Dado** 2 sesiones firmadas y 1 en borrador, **cuando** se filtra con `?estado=firmado`, **entonces** devuelve 2, y un estado inválido da 422 (F04-07). | `test_get_sesiones_filtro_estado` |
| **Dado** el secreto configurado, **cuando** el webhook trae el HMAC correcto, con o sin prefijo `sha256=`, **entonces** 200 (F04-08). | `test_webhook_hmac_valido_200` |
| **Dado** un HMAC de otro secreto o de otro cuerpo, o sin secreto configurado, **cuando** llega el webhook, **entonces** 401 `{"detail": "firma_invalida"}` y la sesión sigue en `borrador` (F04-09). Mutación: hacer que `_verificar_hmac` acepte cualquier firma hace fallar F04-09 y F04-10. | `test_webhook_hmac_invalido_401` |
| **Dado** un webhook sin cabecera `X-Signature`, **cuando** llega, **entonces** 401 y la sesión no cambia (F04-10). | `test_webhook_hmac_ausente_401` |
| **Dado** un webhook válido, **cuando** se relee la sesión, **entonces** está `firmado` con hash, sello de tiempo y certificado; repetirlo da 409 y con otro tenant 404 (F04-11). | `test_webhook_actualiza_estado` |

## 6. Trazabilidad

- Ficha: `governance/tareas/FIRMA-05.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Depende de FIRMA-03 (motor y tabla) y FIRMA-04 (router y webhook).
- La convención `FILAS = []` la establece `tests/test_matriz_permisos.py`; los archivos de matriz son obligatorios para que ese verificador pase.
