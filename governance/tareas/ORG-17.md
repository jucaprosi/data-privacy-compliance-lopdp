+++
id = "ORG-17"
titulo = "Inventario de activos y sistemas, soportes y personas mínimas de la organización"
ola = "backlog"
estado = "pendiente"
sala = "organizacion, frontend"
depende_de = ["ORG-07", "FE-22", "ORG-16"]
propiedad = ["alembic/versions/*_inventario_activos.py", "features/organizacion/services/inventario_engine.py", "features/organizacion/organizacion_service.py#ORG-17", "api/routers/organizacion_inventario.py", "tests/test_organizacion_inventario.py", "tests/test_matriz_permisos.py#ORG-17", "frontend/src/components/organizacion/inventario/**", "frontend/tests/organizacion/inventario.spec.ts", "frontend/src/components/layout/dashboardNavigation.ts#ORG-17", "frontend/src/app/dashboard/page.tsx#ORG-17"]
arbitro = "pytest tests/test_organizacion_inventario.py contra una rama Neon de revisión con lopdp_app + suite completa + Playwright de frontend/tests/organizacion/inventario.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤rbac-tenant", "¤inventario"]
+++

# ORG-17 · Inventario de activos y sistemas, soportes y personas mínimas de la organización

**Origen.** Menú 3 «Inventario» y conflicto D-6 de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md` (fase 2 del documento maestro). En backlog hasta que el propietario lo lance.

## Entrega
- Activos y sistemas, soportes (físicos y digitales) y personas mínimas (nombre, cargo, área, correo; la cédula solo si la firma la exige, cifrada), por organización, vinculables a tratamientos del RAT por la compuerta de `rat`.
- Pantallas en el menú Inventario (secciones `#ORG-17`).
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10: la que se fusione después se vuelve a encadenar). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).

## Límites
- «Titulares» no es una base de titulares: solo colectivos y registros de consentimiento (D-6), fuera de esta tarea.
