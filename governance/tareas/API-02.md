+++
id = "API-02"
titulo = "API de integración versionada: claves por organización con alcance, contrato OpenAPI autenticado y webhooks firmados HMAC-SHA256"
ola = "C"
estado = "pendiente"
sala = "pasillo_central, frontend"
depende_de = ["SEC-13", "OPS-07"]
propiedad = ["app_core/integraciones/__init__.py", "app_core/integraciones/claves.py", "app_core/integraciones/webhooks.py", "alembic/versions/20261120_api02_claves_integracion.py", "frontend/src/components/integraciones/IntegracionesView.tsx", "tests/test_api02_integraciones.py"]
arbitro = "pytest tests/test_api02_integraciones.py + suite completa + vigilantes"
rastros = ["¤seguridad", "¤seguridad-tenant", "¤frontend-ide"]
+++
# API-02 · API de integración versionada: claves por organización con alcance, contrato OpenAPI autenticado y webhooks firmados HMAC-SHA256

## Entrega
- Tabla `claves_integracion` con RLS forzada (`tenant_id`, `nombre`, `prefijo`, `hash_sha256`, `alcances[]`, `creada_en`, `rotada_en`, `revocada_en`) y su migración; la clave en claro se muestra una sola vez al crearla.
- Módulo `app_core/integraciones/claves.py` que autentica la cabecera `Authorization: Bearer evk_…`, resuelve la organización y comprueba el alcance (`rat:lectura`, `tareas:lectura`, `evidencias:lectura`), registrando cada uso en `audit_events`.
- Módulo `app_core/integraciones/webhooks.py` que firma cada evento saliente con HMAC-SHA256 (`X-Evydentia-Firma`, `X-Evydentia-Marca-Tiempo`) y reintenta con backoff exponencial.
- Vista `IntegracionesView.tsx` en el menú Organización para crear, rotar y revocar claves y suscribir webhooks, respetando los techos del paquete (§2.3 del PRD).

## Pruebas
- `pytest tests/test_api02_integraciones.py` comprueba el aislamiento por organización y alcance, el `401` de una clave revocada o rotada, que `/api/v1/openapi.json` exige autenticación y que la firma HMAC de un webhook se verifica y rechaza repeticiones (`INV_API_INTEGRATION_SCOPED_KEYS_VERSIONED`).
