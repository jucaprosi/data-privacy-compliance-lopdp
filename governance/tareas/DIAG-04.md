+++
id = "DIAG-04"
titulo = "Asignar los dominios del assessment a responsables de área"
ola = "D"
estado = "pendiente"
sala = "diagnostico, frontend"
depende_de = ["DIAG-03", "ORG-07", "ORG-14", "FE-22"]
propiedad = ["alembic/versions/20261030_diagnostico_asignaciones.py", "features/diagnostico/services/asignacion_engine.py", "features/diagnostico/diagnostico_service.py#DIAG-04", "api/routers/diagnostico_asignaciones.py", "tests/test_diagnostico_asignaciones.py", "tests/test_matriz_permisos.py#DIAG-04", "frontend/src/components/diagnostico/AsignacionDominios.tsx", "frontend/src/lib/diagnostico/asignaciones.ts", "frontend/tests/diagnostico/asignaciones.spec.ts", "frontend/src/components/layout/dashboardNavigation.ts#DIAG-04", "frontend/src/app/dashboard/page.tsx#DIAG-04"]
arbitro = "pytest tests/test_diagnostico_asignaciones.py contra una rama Neon de revisión con lopdp_app + suite completa + Playwright de frontend/tests/diagnostico/asignaciones.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤diagnostico", "¤diagnostico-asignacion"]
+++

# DIAG-04 · Asignar los dominios del assessment a responsables de área

**Origen.** Apartado 6 (DIAG) de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`: asignación de dominios a responsables.

## Entrega
- Asignar cada dominio del assessment a una persona con rol `responsable_area` vigente (estructura de ORG-07, por la compuerta de `organizacion`). Historial de asignaciones.
- Asigna `coordinador` o `implementador`; el `dpo` consulta (D-2). Fila en `tests/test_matriz_permisos.py` sección `#DIAG-04`.
- Pantalla Diagnóstico › Asignación (secciones `#DIAG-04`).
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10: la que se fusione después se vuelve a encadenar). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- No se asigna a quien no tiene rol vigente en esa organización (422); RLS entre organizaciones; el `dpo` recibe 403 al asignar.
- Mutación documentada: aceptar cualquier usuario y comprobar que la prueba del 422 falla.

## Límites
- No cambia quién responde en `DiagnosticCanvas.tsx` (lo tiene EVI-01); restringir la respuesta al asignado es una tarea posterior.
