+++
id = "RAT-07"
titulo = "Colectivos de titulares y registro de consentimientos por finalidad, sin base de titulares"
ola = "D"
estado = "pendiente"
sala = "rat"
depende_de = ["RAT-05", "EVI-02"]
propiedad = ["alembic/versions/20261102_consentimientos.py", "features/rat/domain/consentimiento.py", "features/rat/services/consentimientos_engine.py", "features/rat/rat_service.py#RAT-07", "api/routers/rat_consentimientos.py", "tests/test_rat_consentimientos.py", "tests/matriz/RAT-07.py", "frontend/src/components/modules/rat/Consentimientos.tsx", "frontend/src/lib/rat/consentimientos.ts", "frontend/tests/rat/consentimientos.spec.ts"]
arbitro = "pytest tests/test_rat_consentimientos.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/rat/consentimientos.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤rat", "¤evidencias"]
+++

# RAT-07 · Colectivos de titulares y registro de consentimientos por finalidad, sin base de titulares

**Origen.** Menú 3 «Inventario › Titulares» y conflicto D-6 de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`: solo colectivos y registros de consentimiento, nunca bases de titulares (Doctrina 8).

**Contrato:** `governance/especificaciones/RAT-07.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Colectivos de titulares por tratamiento (clientes, empleados, pacientes…) con la base de legitimación y, si es consentimiento, el modelo de texto vigente y su versión.
- Registro de consentimiento como **evento agregado**: fecha, colectivo, finalidad, versión del texto, canal y cantidad; nunca identidad del titular. Un consentimiento individual con prueba se guarda como evidencia (EVI-02), no como fila de titular.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).

## Pruebas
- El servidor rechaza cualquier campo de identificación de un titular (422); el registro agrega cantidades por día.
- Mutación documentada: aceptar un campo `email` y comprobar que la prueba falla.

## Límites
- No implementa formularios web de consentimiento (Biblioteca, textos web).
