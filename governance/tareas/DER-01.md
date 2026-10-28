+++
id = "DER-01"
titulo = "Solicitudes de titulares: verificación de identidad, modelos de respuesta y la respuesta como evidencia"
ola = "D"
estado = "pendiente"
sala = "derechos_arco, frontend"
depende_de = ["EVI-02", "FE-22"]
propiedad = ["alembic/versions/20261104_derechos_respuestas.py", "features/derechos_arco/services/respuestas_engine.py", "features/derechos_arco/derechos_arco_service.py#DER-01", "api/routers/derechos_respuestas.py", "tests/test_derechos_respuestas.py", "tests/matriz/DER-01.py", "frontend/src/components/derechos/**", "frontend/src/lib/derechos/respuestas.ts", "frontend/tests/derechos/respuestas.spec.ts"]
arbitro = "pytest tests/test_derechos_respuestas.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/derechos/respuestas.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤evidencias", "¤rbac-tenant"]
+++

# DER-01 · Solicitudes de titulares: verificación de identidad, modelos de respuesta y la respuesta como evidencia

**Origen.** Menú 5 «Operación › Solicitudes de titulares» de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md` sobre `derechos_arco_solicitudes` (SEC-09).

**Contrato:** `governance/especificaciones/DER-01.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Verificación de identidad proporcional antes de responder: método (documento, correo verificado, presencial), quién verificó y cuándo; sin ella no se puede responder.
- Modelos de respuesta por derecho y resultado (concedido, denegado, parcial) con variables; la respuesta enviada se custodia como evidencia (EVI-02) vinculada a la solicitud.
- El `responsable_area` o `coordinador` prepara; el `admin_organizacion` o `implementador` aprueba y envía; el `dpo` consulta (decisión 1). **Sin plazo calculado** (LEG-03, REG-01): el semáforo llega con REG-01.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Responder sin verificación de identidad da 409; la respuesta queda como evidencia con el modelo y las variables resueltas; el `dpo` no envía (403).
- Mutación documentada: permitir responder sin verificar y comprobar que la prueba falla.

## Límites
- Sin portal público (DER-02) ni plazos.
