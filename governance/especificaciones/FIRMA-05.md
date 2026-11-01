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
- **R5 · Sin secretos en código.** El secreto del webhook en FIRMA-04.py se genera con `secrets.token_hex(32)` en cada ejecución y se inyecta con `monkeypatch.setenv`.

## 4. Interfaz

Sin interfaz.

## 5. Aceptación

### Matriz FIRMA-03 (10 casos)

| ID | Escenario |
| :--- | :--- |
| F03-01 | Crear sesión persiste en BD y se puede releer |
| F03-02 | `marcar_firmado` transiciona a `firmado` con hash, TSA y certificado |
| F03-03 | Doble `marcar_firmado` lanza `TransicionFirmaInvalidaError` |
| F03-04 | `marcar_firmado` sobre firma inexistente lanza `SesionFirmaNoEncontradaError` |
| F03-05 | Tenant B no ve sesión de tenant A (`obtener_sesion` devuelve `None`) |
| F03-06 | Tenant B no puede insertar filas de tenant A (`42501` WITH CHECK) |
| F03-07 | `lopdp_app` no puede reescribir `sha256_original` (`42501`) |
| F03-08 | `lopdp_app` no puede borrar la sesión (`42501`) |
| F03-09 | Evento de auditoría `crear_sesion_firma` existe tras crear |
| F03-10 | Dos eventos de auditoría tras crear y firmar |

### Matriz FIRMA-04 (11 casos)

| ID | Escenario |
| :--- | :--- |
| F04-01 | `POST /firma/sesiones` crea sesión en `borrador`; tenant B no la ve |
| F04-02 | `GET /firma/sesiones/{id}` devuelve la sesión de su tenant |
| F04-03 | `GET /firma/sesiones/{id}` desde tenant B devuelve 404 |
| F04-04 | `GET /firma/sesiones` lista vacía para tenant sin sesiones |
| F04-05 | Webhook HMAC válido pasa la sesión a `firmado` |
| F04-06 | Webhook HMAC con `sha256=` como prefijo también es válido |
| F04-07 | Webhook con HMAC de otro secreto devuelve 401 |
| F04-08 | Webhook sin cabecera `X-Signature` devuelve 401 |
| F04-09 | Webhook sin secreto configurado devuelve 401 (falla cerrada) |
| F04-10 | Filtro `?estado=firmado` devuelve solo las firmadas |
| F04-11 | Filtro `?estado=` inválido devuelve 422 |

## 6. Trazabilidad

- Ficha: `governance/tareas/FIRMA-05.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Depende de FIRMA-03 (motor y tabla) y FIRMA-04 (router y webhook).
- La convención `FILAS = []` la establece `tests/test_matriz_permisos.py`; los archivos de matriz son obligatorios para que ese verificador pase.
