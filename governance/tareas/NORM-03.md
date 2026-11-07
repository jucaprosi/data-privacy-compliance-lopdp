+++
id = "NORM-03"
titulo = "Análisis de impacto de una resolución con Gemini, validado por persona, y regeneración de la caché de contexto"
ola = "D"
estado = "pendiente"
sala = "inteligencia_normativa, ai_copilot"
depende_de = ["NORM-01", "VTX-01"]
propiedad = ["alembic/versions/20261104_norm03_analisis_impacto.py", "features/inteligencia_normativa/inteligencia_normativa_service.py#NORM-03", "features/inteligencia_normativa/domain/errores.py#NORM-03", "features/inteligencia_normativa/services/impacto.py", "features/inteligencia_normativa/services/extraccion.py", "features/ai_copilot/copilot_service.py#NORM-03", "app_core/pasillo/ai_copilot.py#NORM-03", "app_core/pasillo/regulacion_rag.py#NORM-03", "api/routers/inteligencia_normativa_impacto.py", "tests/test_norm03_impacto_hitl.py", "frontend/src/components/normativa_impacto/**", "frontend/tests/normativa_impacto/**"]
arbitro = "pytest tests/test_norm03_impacto_hitl.py contra un PostgreSQL 16 local en contenedor + suite completa + Playwright de frontend/tests/normativa_impacto + tsc --noEmit + npm run build"
rastros = ["¤inteligencia-normativa", "¤copiloto-ia", "¤vertex-cache", "¤dpo-independencia"]
+++
# NORM-03 · Análisis de impacto de una resolución con Gemini, validado por persona, y regeneración de la caché de contexto

**Origen.** `PRD_EVYDENTIA_REVENTA_NUBE.md`, Módulo 6.3 (fase 2 de BRF-001), con el principio de validación humana inviolable. El tablero `TASKS_EVYDENTIA_REVENTA_NUBE.md` la citaba (BL-189, tanda 45) sin ficha.

**Contrato:** `governance/especificaciones/NORM-03.md`.

## Entrega
- Extracción y división en fragmentos del texto de una resolución en `services/extraccion.py`, a partir del original de NORM-01. Los vectores se indexan con `text-embedding-005` por el pasillo de `regulacion_rag`.
- Análisis de impacto en `services/impacto.py` con `gemini-2.5-pro`, por la compuerta del copiloto. Para cada organización propone qué preguntas del assessment, fichas del RAT, tareas del plan y plantillas afecta la resolución, citando sus artículos. La salida sigue un esquema Pydantic.
- Tabla `normativa_analisis_impacto` por organización, con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`). La propuesta queda `propuesta` hasta que el DPO la acepte o la rechace; aceptar no cambia nada por sí solo, sino que genera hallazgos hacia el plan de acción único.
- Cuando una resolución pasa a `vigente`, `reformada` o `derogada` (NORM-02), cambia el `corpus_sha256` y se pide a VTX-01 regenerar la caché de contexto, por el pasillo.
- Router propio `api/routers/inteligencia_normativa_impacto.py` y componentes en `frontend/src/components/normativa_impacto/**`, que se montan en la pantalla de NORM-02.

## Decisiones asumidas
- El costo del análisis cae dentro del tope de IA por organización de SEC-13 cuando esa tarea esté integrada; no es dependencia.
- Antes de llamar al modelo, el texto pasa por el filtro DLP Módulo 10 de VTX-01 (las resoluciones son públicas, pero el contexto de la organización no).

## Pruebas
- `pytest tests/test_norm03_impacto_hitl.py`, con el modelo simulado, comprueba:
  - que la propuesta cita artículos de la resolución y declara la falta de base cuando no la hay;
  - que nada cambia en el assessment ni en el RAT sin la aceptación del DPO;
  - que aceptar genera hallazgos;
  - el aislamiento RLS entre organizaciones;
  - que el cambio de estado pide regenerar la caché.
