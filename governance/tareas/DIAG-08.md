+++
id = "DIAG-08"
titulo = "Escala SMARTCIDI en el servidor: nivel asignado 1 a 5 y evidencia 0 a 4 por control, nivel por dimensión y sin cifra global de la organización"
ola = "D"
estado = "hecha"
sala = "diagnostico"
depende_de = ["DIAG-03", "DIAG-02", "DIAG-01", "RM-21"]
propiedad = ["alembic/versions/20261031_diagnostico_escala_smartcidi.py", "features/diagnostico/domain/models.py", "features/diagnostico/domain/resultados.py", "features/diagnostico/services/dimensiones_sgpdp.py", "features/diagnostico/services/resultados_engine.py", "features/diagnostico/services/respuestas_engine.py", "features/diagnostico/services/engine.py", "features/diagnostico/services/report_generator.py", "features/diagnostico/diagnostico_service.py#DIAG-08", "api/routers/diagnostico.py", "api/routers/diagnostico_respuestas.py", "api/routers/diagnostico_resultados.py", "tests/test_diagnostico_escala_smartcidi.py", "tests/test_diagnostico_respuestas.py", "tests/test_diagnostico_resultados.py", "tests/test_assessment_matriz.py", "tests/test_diagnostico_timebox.py", "features/roadmap/services/contexto_generacion.py", "features/roadmap/services/hallazgo_engine.py", "governance/contratos/hoja_de_ruta.openapi.json", "tests/test_api_gateway.py", "tests/test_roadmap_hallazgos.py", "tests/test_roadmap_generacion_en_linea.py", "tests/test_roadmap_contexto_real.py", "tests/test_e2e_hoja_de_ruta_real.py", "tests/test_roadmap_control_ref.py", "tests/test_roadmaps_api.py", "tests/test_contrato_hoja_ruta.py"]
arbitro = "pytest tests/test_diagnostico_escala_smartcidi.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + vigilantes; prueba de mutación documentada"
rastros = ["¤diagnostico", "¤diagnostico-scoring"]
+++

# DIAG-08 · Escala SMARTCIDI en el servidor

**Decisión del propietario (2026-10-29), que sustituye a la de la escala 0–3 del 2026-10-28.** La madurez de las preguntas del diagnóstico sigue la metodología del archivo de assessment SMARTCIDI (`data/Assessment_Madurez_SGPDP_COAC_SMARTCIDI (2).xlsx`, hojas «Niveles de Madurez», «Catálogos» y «Guía Aplicación Comercio»): **nivel asignado 1 a 5** y **nivel de evidencia 0 a 4** por control; el nivel efectivo es el menor entre el asignado y la evidencia más uno. La app había reducido la respuesta a tres estados (Implementado, Parcial, No implementado → 5, 3, 1) y la evidencia a cuatro (E0–E3), y el PRD fijaba una tercera escala 0–3 que ningún código usaba.

**Contrato:** `governance/especificaciones/DIAG-08.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Migración: `diagnostico_respuestas` gana `nivel_asignado` (1 a 5, nulo = sin responder con la escala nueva) y la evidencia pasa de 0–3 a 0–4, con la correspondencia del contrato para las filas existentes.
- `PUT /diagnostico/respuestas` recibe `nivel_asignado` y `nivel_evidencia`; el **estado de conformidad deja de ser una entrada**: el servidor lo deriva del nivel asignado, de modo que la hoja de ruta, el preanálisis y los hallazgos siguen leyendo el mismo campo.
- El motor (`dimensiones_sgpdp.py`) toma el nivel asignado tal cual, sin la tabla de tres estados; el sellado guarda los indicadores **por dimensión** (nivel 0 a 5 con su etiqueta) y deja de guardar la madurez global, el nivel global y el riesgo residual como complemento del puntaje.
- Se retira el motor heredado de madurez 0–3 (`ScoringDiagnostico.madurez_spdp` en `engine.py`) y los informes de `api/routers/diagnostico.py` pasan a los niveles por dimensión.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`) ni la rama compartida `test`.

## Pruebas
- La escala, la regla del nivel efectivo, la derivación del estado y los indicadores por dimensión, según los escenarios del contrato.
- Mutación documentada: volver a la tabla de tres estados (Conforme → 5) hace fallar la prueba del nivel asignado 2 y 4.

## Límites
- No toca la pantalla: el formulario de respuesta, el panel ejecutivo y los reportes del navegador son de DIAG-09; el tablero, de FE-24.
- No edita los resultados ya sellados (inmutables): se leen con su escala anterior.
- Si una prueba fuera de la lista de propiedad se rompe por el cambio de escala, detente e informa; no la edites.
