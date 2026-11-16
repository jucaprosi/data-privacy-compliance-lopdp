# API-02 · API de integración versionada: claves por organización con alcance, contrato OpenAPI autenticado y webhooks firmados HMAC-SHA256
`¤sdd` `¤api-integraciones` `¤grado-productivo` `¤seguridad` `¤seguridad-tenant`

## 1. Datos

Clave `ClaveIntegracion` (`id: UUID`, `tenant_id: UUID`, `nombre: str`, `prefijo: str`, `hash_sha256: str`, `alcances: list[str]`, `revocada_en: datetime | None`). Suscripción `SuscripcionWebhook` (`tenant_id: UUID`, `url: HttpUrl`, `eventos: list[str]`, `secreto_ref: str`).

## 2. API

- `POST /api/v1/integraciones/claves` (Administrador) -> `201` con la clave en claro una sola vez.
- `POST /api/v1/integraciones/claves/{id}/rotar` y `DELETE /api/v1/integraciones/claves/{id}` -> `200` / `204`.
- `GET /api/v1/openapi.json` -> `200` solo con sesión o clave válida; `401` sin ella.
- `POST /api/v1/integraciones/webhooks` -> `201` con la suscripción.

## 3. Reglas

- **R1 · Una clave, una organización (`INV_API_INTEGRATION_SCOPED_KEYS_VERSIONED`).** Una clave solo accede a los recursos de su organización y de sus alcances; la RLS lo garantiza también en la base.
- **R2 · Solo hash.** La clave se guarda como hash SHA-256; la rotación y la revocación tienen efecto inmediato.
- **R3 · Contrato estable.** Una versión publicada de la API (`/api/v1`) no cambia su contrato de forma incompatible: los cambios incompatibles van en `/api/v2`.
- **R4 · Webhooks verificables.** Todo evento saliente lleva firma HMAC-SHA256 y marca de tiempo; el receptor rechaza firmas inválidas o eventos con más de 5 minutos.

## 4. Interfaz

Pantalla «Integraciones» en el menú Organización: lista de claves con prefijo, alcances y último uso; botones Crear, Rotar y Revocar; lista de webhooks con su estado de entrega.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una clave de la organización A con alcance `rat:lectura`, **cuando** pide tareas o datos de la organización B, **entonces** recibe `403` y el intento queda en `audit_events`. | `test_clave_aislada_por_organizacion_y_alcance` |
| **Dado** una clave revocada, **cuando** se usa en cualquier ruta, **entonces** recibe `401`. | `test_clave_revocada_rechazada` |
| **Dado** un cliente sin sesión ni clave, **cuando** pide `/api/v1/openapi.json`, **entonces** recibe `401`. | `test_openapi_requiere_autenticacion` |
| **Dado** un webhook firmado con el secreto de la suscripción, **cuando** se verifica su firma y su marca de tiempo, **entonces** la firma es válida y la repetición del mismo evento pasados 5 minutos se rechaza. | `test_webhook_firmado_y_sin_repeticion` |

## 6. Trazabilidad

- PRD §2.3, §5.4 pilar 4 y criterio 32; invariante `INV_API_INTEGRATION_SCOPED_KEYS_VERSIONED`.
