+++
id = "DPO-03"
titulo = "Consultas de la organización al DPO con historial como evidencia de asesoría"
ola = "D"
estado = "pendiente"
sala = "dpo_cockpit, frontend"
depende_de = ["DPO-02", "EVI-02"]
propiedad = ["alembic/versions/20261104_dpo_consultas.py", "features/dpo_cockpit/domain/consulta.py", "features/dpo_cockpit/services/consultas_engine.py", "features/dpo_cockpit/dpo_cockpit_service.py#DPO-03", "api/routers/dpo_consultas.py", "tests/test_dpo_consultas.py", "tests/matriz/DPO-03.py", "frontend/src/components/dpo/Consultas.tsx", "frontend/src/lib/dpo/consultas.ts", "frontend/tests/dpo/consultas.spec.ts", "frontend/src/components/layout/menus/DPO-03.ts", "frontend/src/components/layout/pantallas/DPO-03.tsx"]
arbitro = "pytest tests/test_dpo_consultas.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/dpo/consultas.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤dpo-cockpit", "¤evidencias"]
+++

# DPO-03 · Consultas de la organización al DPO con historial como evidencia de asesoría

**Origen.** Menú 5 «Operación › Consultas» y menú 7 «DPO › Consultas atendidas» de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Contrato:** `governance/especificaciones/DPO-03.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Tickets de consulta de cualquier rol de la organización al DPO: asunto, texto, adjuntos por referencia; el DPO responde y cierra; la respuesta entra en su bitácora (DPO-01) como `OPINION_CONSULTIVA` y el hilo se custodia como evidencia de asesoría (EVI-02).
- Pantallas: Operación › Consultas (quien pregunta) y DPO › Consultas atendidas.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Solo el `dpo` responde y cierra; al cerrar existe una entrada en la bitácora y una evidencia; una consulta de A no se ve desde B.
- Mutación documentada: cerrar sin crear la entrada de bitácora y comprobar que la prueba falla.

## Límites
- Sin plazos de respuesta.
