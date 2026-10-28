+++
id = "DER-02"
titulo = "Portal público de solicitudes de titulares por organización, con enlace de seguimiento"
ola = "D"
estado = "pendiente"
sala = "derechos_arco, frontend"
depende_de = ["DER-01", "SEC-12"]
propiedad = ["alembic/versions/20261105_derechos_portal.py", "features/derechos_arco/services/portal_engine.py", "features/derechos_arco/derechos_arco_service.py#DER-02", "api/routers/publico_derechos.py", "tests/test_derechos_portal.py", "frontend/src/app/solicitud/**", "frontend/tests/derechos/portal.spec.ts"]
arbitro = "pytest tests/test_derechos_portal.py contra una rama Neon de revisión + suite completa + Playwright de frontend/tests/derechos/portal.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada; cumple el diseño de SEC-12"
rastros = ["¤seguridad", "¤rbac-tenant"]
+++

# DER-02 · Portal público de solicitudes de titulares por organización, con enlace de seguimiento

**Origen.** Menú 5 y conflicto D-7 de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`: portal público con las precondiciones de seguridad de SEC-12.

**Contrato:** `governance/especificaciones/DER-02.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Página pública `/solicitud/<organizacion>` con la marca de la organización: tipo de derecho, datos de contacto mínimos y descripción; crea la solicitud y devuelve un código de seguimiento.
- Seguimiento `/solicitud/seguir/<codigo>`: solo estado y fechas, nunca el contenido de la respuesta ni datos de otros titulares.
- Límites de abuso según SEC-12 (tasa por IP, tamaño de adjuntos, sin enumeración de organizaciones).
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Un código de seguimiento ajeno no revela nada (404 uniforme); más de N solicitudes por IP y hora responden 429; la solicitud creada aparece en la bandeja interna.
- Mutación documentada: devolver el contenido de la respuesta en el seguimiento y comprobar que la prueba falla.

## Límites
- Sin cuenta de titular; sin plazos.
