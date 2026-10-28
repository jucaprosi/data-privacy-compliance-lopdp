+++
id = "DIAG-05"
titulo = "«No aplica» exige justificación en el assessment"
ola = "D"
estado = "pendiente"
sala = "diagnostico, frontend"
depende_de = ["DIAG-01", "DIAG-03", "EVI-01"]
propiedad = ["alembic/versions/20261030_diagnostico_no_aplica.py", "features/diagnostico/services/respuestas_engine.py", "features/diagnostico/diagnostico_service.py#DIAG-05", "api/routers/diagnostico_respuestas.py", "tests/test_diagnostico_no_aplica.py", "frontend/src/lib/diagnostico/clienteRespuestas.ts", "frontend/src/components/DiagnosticCanvas.tsx", "frontend/tests/diagnostico/no-aplica.spec.ts"]
arbitro = "pytest tests/test_diagnostico_no_aplica.py y tests/test_diagnostico_respuestas.py contra una rama Neon de revisión + suite completa + Playwright de frontend/tests/diagnostico + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤diagnostico", "¤diagnostico-no-aplica"]
+++

# DIAG-05 · «No aplica» exige justificación en el assessment

**Origen.** Conflicto D-8 de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`: se adopta la justificación obligatoria de «no aplica» (la escala sigue 0–3, decisión del propietario del 2026-10-28).

## Entrega
- Una respuesta «no aplica» sin justificación (texto no vacío, con longitud mínima) se rechaza en el servidor con 422; la justificación se guarda con la respuesta y su autor.
- `DiagnosticCanvas.tsx` pide la justificación al marcar «no aplica» y la muestra al revisar.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10: la que se fusione después se vuelve a encadenar). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).

## Pruebas
- 422 sin justificación; con ella, sobrevive a una sesión nueva.
- Mutación documentada: aceptar «no aplica» sin texto y comprobar que la prueba falla.

## Límites
- Espera a EVI-01, que también escribe `DiagnosticCanvas.tsx`.
