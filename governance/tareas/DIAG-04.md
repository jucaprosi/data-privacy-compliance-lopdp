+++
id = "DIAG-04"
titulo = "El administrador asigna los dominios del assessment a encargados del diagnóstico"
ola = "D"
estado = "pendiente"
sala = "diagnostico, frontend"
depende_de = ["DIAG-03", "ORG-07", "ORG-14", "FE-22", "RM-21"]
propiedad = ["alembic/versions/20261030_diagnostico_asignaciones.py", "features/diagnostico/services/asignacion_engine.py", "features/diagnostico/diagnostico_service.py#DIAG-04", "api/routers/diagnostico_asignaciones.py", "tests/test_diagnostico_asignaciones.py", "tests/matriz/DIAG-04.py", "frontend/src/components/diagnostico/AsignacionDominios.tsx", "frontend/src/lib/diagnostico/asignaciones.ts", "frontend/tests/diagnostico/asignaciones.spec.ts", "frontend/src/components/layout/menus/DIAG-04.ts", "frontend/src/components/layout/pantallas/DIAG-04.tsx"]
arbitro = "pytest tests/test_diagnostico_asignaciones.py contra una rama Neon de revisión con lopdp_app + suite completa + Playwright de frontend/tests/diagnostico/asignaciones.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤diagnostico", "¤diagnostico-asignacion"]
+++

# DIAG-04 · El administrador asigna los dominios del assessment a encargados del diagnóstico

**Origen.** Apartado 6 (DIAG) de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`. **Decisión del propietario (2026-10-28):** el diagnóstico ocurre antes de implementar la LOPDP, cuando aún no hay responsables de área; por eso el administrador asigna cada dominio a un **encargado del diagnóstico**, cualquier persona con rol vigente en la organización (si ya existen responsables de área, serán ellos). Quién responde y cómo revisa el DPO es DIAG-07.

**Contrato:** `governance/especificaciones/DIAG-04.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Asignar cada dominio del assessment (dimensiones D01–D10) a una persona con **cualquier rol vigente** en la organización salvo `dpo` (por la compuerta de `organizacion`). Historial de asignaciones.
- Asigna `admin_organizacion`; `implementador`, `coordinador` y `dpo` consultan (D-2). Sus filas de la matriz en `tests/matriz/DIAG-04.py`.
- Pantalla Diagnóstico › Asignación (`frontend/src/components/layout/menus/DIAG-04.ts` y `frontend/src/components/layout/pantallas/DIAG-04.tsx`).
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10: la que se fusione después se vuelve a encadenar). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- No se asigna a quien no tiene rol vigente en esa organización ni al `dpo` (422); RLS entre organizaciones; `dpo`, `coordinador` e `implementador` reciben 403 al asignar.
- Mutación documentada: aceptar cualquier usuario y comprobar que la prueba del 422 falla.

## Límites
- No cambia quién responde en `DiagnosticCanvas.tsx` (lo tiene EVI-01); restringir la respuesta al asignado es DIAG-07.
