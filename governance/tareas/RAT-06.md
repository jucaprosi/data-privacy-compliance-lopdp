+++
id = "RAT-06"
titulo = "Exportación completa del RAT a XLSX y PDF con la versión vigente de cada ficha"
ola = "D"
estado = "pendiente"
sala = "rat"
depende_de = ["RAT-05"]
propiedad = ["features/rat/services/exportacion_engine.py", "features/rat/rat_service.py#RAT-06", "api/routers/rat_exportacion.py", "tests/test_rat_exportacion.py", "tests/matriz/RAT-06.py", "frontend/src/components/modules/rat/ExportarRat.tsx", "frontend/tests/rat/exportacion.spec.ts"]
arbitro = "pytest tests/test_rat_exportacion.py contra una rama Neon de revisión + suite completa + Playwright de frontend/tests/rat/exportacion.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤rat"]
+++

# RAT-06 · Exportación completa del RAT a XLSX y PDF con la versión vigente de cada ficha

**Origen.** Menú 3 «Inventario › Tratamientos» (exportar) de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Contrato:** `governance/especificaciones/RAT-06.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- `GET /rat/exportar?formato=xlsx|pdf`: todas las fichas vigentes de la organización, una fila por tratamiento, con la fecha y el número de versión; el PDF lleva la huella SHA-256 del XLSX en el pie.
- Lo descargan los roles de lectura del RAT.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).

## Pruebas
- El XLSX tiene tantas filas como fichas vigentes y ninguna dada de baja; el PDF lleva la huella.
- Mutación documentada: incluir fichas dadas de baja y comprobar que la prueba falla.

## Límites
- Sin mapa visual de flujos (fuera del alcance).
