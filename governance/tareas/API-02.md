+++
id = "API-02"
titulo = "Claves de integración por organización con techo del paquete"
ola = "C"
estado = "pendiente"
sala = "pasillo_central, frontend"
depende_de = ["SEC-13", "OPS-07", "BOV-01"]
propiedad = ["alembic/versions/api02_claves_integracion.py", "app_core/integraciones/__init__.py", "app_core/integraciones/claves.py", "app_core/integraciones/techos.py", "api/routers/integraciones_claves.py", "tests/test_api02_integraciones.py", "tests/matriz/API-02.py", "frontend/src/components/integraciones/IntegracionesView.tsx", "frontend/src/lib/integraciones/clavesIntegracion.ts", "frontend/src/components/layout/menus/API-02.ts", "frontend/src/components/layout/pantallas/API-02.tsx", "frontend/src/components/layout/menus/index.ts#API-02", "frontend/src/components/layout/pantallas/index.tsx#API-02", "frontend/tests/integraciones/integraciones.spec.ts"]
crea = ["alembic/versions/api02_claves_integracion.py", "app_core/integraciones/__init__.py", "app_core/integraciones/claves.py", "app_core/integraciones/techos.py", "api/routers/integraciones_claves.py", "tests/test_api02_integraciones.py", "tests/matriz/API-02.py", "frontend/src/components/integraciones/IntegracionesView.tsx", "frontend/src/lib/integraciones/clavesIntegracion.ts", "frontend/src/components/layout/menus/API-02.ts", "frontend/src/components/layout/pantallas/API-02.tsx", "frontend/tests/integraciones/integraciones.spec.ts"]
siembra = ["app_core/integraciones/techos.py#API-02b", "frontend/src/components/integraciones/IntegracionesView.tsx#API-02b"]
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

## Partición (Arquitecto ADPA, 2026-11-13; aprobada por el CTO)
Esta ficha se queda con las claves; los webhooks firmados pasan a `API-02b`. `app_core/integraciones/webhooks.py` sale de la propiedad.

**Entrega.**
- Rutas en `api/routers/integraciones_claves.py`: `POST /api/v1/integraciones/claves`, `GET /claves`, `POST /claves/{id}/rotar`, `POST /claves/{id}/revocar` y `GET /api/v1/integraciones/techos`.
- `GET /techos` devuelve `{claves:{maximo,activas}, webhooks:{maximo,activos}}`. El máximo lo da `techos_integracion(tenant)` de BOV-01 por `app_core/pasillo/boveda_cloud.py`; `activos = 0` hasta API-02b (sección `techos.py#API-02b`, sembrada vacía aquí).
- Crear devuelve 409 `TECHO_CLAVES_ALCANZADO` si activas ≥ máximo; una clave revocada no cuenta.
- Escriben `admin_organizacion` y `coordinador`; el DPO solo consulta.
- La clave en claro solo en la respuesta de crear y de rotar.
- `claves_integracion` con RLS ENABLE+FORCE; `lopdp_app` con SELECT, INSERT y UPDATE (solo `rotada_en` y `revocada_en`; un trigger impide cambiar hash y prefijo), sin DELETE.
- Migración sin fecha `api02_claves_integracion.py`, con FUSION_ALEMBIC sobre la de BOV-01.
- Menú «Configuración» (grupo `configuracion`). `IntegracionesView.tsx` siembra vacía la sección `#API-02b`.

**Árbitro.** `pytest tests/test_api02_integraciones.py` + `test_matriz_permisos.py` + Playwright `frontend/tests/integraciones/integraciones.spec.ts` + `tsc --noEmit` + build.

**Mutaciones.** m1 aceptar una clave revocada → falla el 401; m2 crear sobre el techo → falla; m3 el DPO crea → falla la matriz; m4 la clave en claro en el GET → falla; m5 el trigger permite cambiar el hash → falla.

**Orden de fusión.** BOV-01 (con su enmienda) → API-02 → API-02b. **Pasa por UX/UI antes de lanzarse.**
