+++
id = "API-02b"
titulo = "Webhooks firmados HMAC-SHA256 con techo del paquete"
ola = "backlog"
estado = "pendiente"
sala = "pasillo_central, frontend"
depende_de = ["API-02", "BOV-01"]
propiedad = ["alembic/versions/api02b_webhooks_suscripciones.py", "app_core/integraciones/webhooks.py", "app_core/integraciones/techos.py#API-02b", "api/routers/integraciones_webhooks.py", "tests/test_api02b_webhooks.py", "tests/matriz/API-02b.py", "frontend/src/components/integraciones/IntegracionesView.tsx#API-02b", "frontend/src/components/integraciones/WebhooksPanel.tsx", "frontend/src/lib/integraciones/webhooks.ts", "frontend/tests/integraciones/webhooks.spec.ts"]
crea = ["alembic/versions/api02b_webhooks_suscripciones.py", "app_core/integraciones/webhooks.py", "api/routers/integraciones_webhooks.py", "tests/test_api02b_webhooks.py", "tests/matriz/API-02b.py", "frontend/src/components/integraciones/WebhooksPanel.tsx", "frontend/src/lib/integraciones/webhooks.ts", "frontend/tests/integraciones/webhooks.spec.ts"]
arbitro = "pytest tests/test_api02b_webhooks.py + test_matriz_permisos.py + Playwright frontend/tests/integraciones/webhooks.spec.ts + tsc --noEmit + build; mutaciones m1 a m5"
rastros = ["¤seguridad", "¤seguridad-tenant", "¤frontend-ide"]
+++

# API-02b · Webhooks firmados HMAC-SHA256 con techo del paquete

Diseño del Arquitecto ADPA (2026-11-13), hija de `API-02`. **Pasa por UX/UI antes de lanzarse.** Las dos secciones `#API-02b` las siembra API-02 al crear sus archivos.

## Entrega
- Rutas en `api/routers/integraciones_webhooks.py`: `POST /api/v1/integraciones/webhooks`, `GET /webhooks`, `POST /webhooks/{id}/rotar-secreto` y `POST /webhooks/{id}/desactivar`.
- Tabla `webhooks_suscripciones` (`tenant_id`, `url`, `eventos[]`, `secreto_cifrado`, `activo`, `creada_en`, `rotada_en`) con RLS ENABLE+FORCE, sin DELETE. El secreto va cifrado, porque hace falta para firmar; el cifrado lo confirma Seguridad.
- Solo `https`; se rechazan IP privadas, loopback y de metadatos (169.254.169.254) tras resolver el nombre. `eventos`, de un catálogo cerrado.
- Firma HMAC-SHA256 en `X-Evydentia-Firma`, con `X-Evydentia-Marca-Tiempo` y ventana de 5 minutos; reintento con backoff.
- 409 `TECHO_WEBHOOKS_ALCANZADO`; el recuento de activos, en `techos.py#API-02b`.
- Migración sin fecha `api02b_webhooks_suscripciones.py`, con FUSION_ALEMBIC.

## Mutaciones
m1 otro secreto → falla la verificación; m2 marca de tiempo vieja aceptada → falla; m3 URL interna aceptada → falla; m4 crear sobre el techo → falla; m5 el secreto en claro en el GET → falla.
