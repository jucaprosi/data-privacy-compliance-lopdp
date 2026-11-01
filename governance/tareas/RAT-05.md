+++
id = "RAT-05"
titulo = "Validaciones del RAT por regla y versionado de cada ficha de tratamiento"
ola = "D"
estado = "pendiente"
sala = "rat"
depende_de = ["RAT-04", "RM-21", "RAT-03", "CAPA-02"]
propiedad = ["alembic/versions/20261102_rat_versiones.py", "features/rat/domain/validaciones.py", "features/rat/services/validaciones_engine.py", "features/rat/services/versiones_engine.py", "features/rat/rat_service.py#RAT-05", "api/routers/rat_validaciones.py", "tests/test_rat_validaciones.py", "tests/matriz/RAT-05.py", "frontend/src/components/modules/rat/ValidacionesFicha.tsx", "frontend/src/lib/rat/validaciones.ts", "frontend/tests/rat/validaciones.spec.ts", "features/roadmap/domain/hallazgo.py#RAT-05", "features/roadmap/services/hallazgo_cierre_engine.py#RAT-05", "features/roadmap/roadmap_service.py#RAT-05", "api/routers/roadmaps_hallazgos.py#RAT-05", "app_core/pasillo/roadmap.py#RAT-05", "features/rat/domain/models.py#RAT-05", "features/rat/services/rat_engine.py#RAT-05", "api/routers/rat.py#RAT-05", "frontend/src/components/modules/RatModule.tsx#RAT-05", "tests/test_compliance_graph.py#RAT-05", "tests/test_rat_eipd.py#RAT-05", "tests/test_rat_persistencia.py#RAT-05", "tests/test_rat_plantilla_salud.py#RAT-05", "tests/test_roadmap_contexto_real.py#RAT-05"]
arbitro = "pytest tests/test_rat_validaciones.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/rat/validaciones.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤rat", "¤hallazgos"]
+++

# RAT-05 · Validaciones del RAT por regla y versionado de cada ficha de tratamiento

**Origen.** Menú 3 «Inventario › Tratamientos (RAT)» y optimización O-2 de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`: un campo no conforme se muestra en rojo y genera hallazgo; cada cambio crea versión.

**Contrato:** `governance/especificaciones/RAT-05.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Reglas de validación de una ficha RAT (en código, hasta que REG-01 las lleve al paquete normativo): datos sensibles exigen condición habilitante; menores, perfilamiento o biometría marcan para EIPD; base de legitimación obligatoria; plazo de conservación obligatorio.
- Cada guardado de una ficha crea una versión inmutable con autor y fecha; dar de baja conserva el histórico.
- Una ficha con una regla incumplida produce un hallazgo por la compuerta de `roadmap` (`registrar_hallazgo`, origen `rat`, clave `ficha:regla`), idempotente; al corregirla el hallazgo se cierra.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).

## Pruebas
- Una ficha con datos sensibles sin condición genera exactamente un hallazgo; corregida, se cierra; dos guardados crean dos versiones.
- Mutación documentada: validar sin generar hallazgo y comprobar que la prueba falla.

## Límites
- No cambia el formulario del RAT salvo el panel de validaciones y el campo `condicion_habilitante`; la exportación es RAT-06.
- La propiedad se amplió antes de implementar (decisión del coordinador del 2026-10-31): sin origen `rat`, sin `condicion_habilitante` y sin engancharse al guardado el contrato no se podía cumplir.
