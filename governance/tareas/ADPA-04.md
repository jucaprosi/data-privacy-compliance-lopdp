+++
id = "ADPA-04"
titulo = "Retirar deuda lateral ADPA lote 2 (riesgos_mtge, roadmap) y sellar DEUDA_LATERAL = 0"
ola = "C"
estado = "pendiente"
sala = "riesgos_mtge, roadmap"
depende_de = ["ADPA-03", "DIAG-08", "DIAG-13", "RM-23"]
propiedad = ["app_core/pasillo/rat.py#ADPA-04", "app_core/pasillo/organizacion.py#ADPA-04", "features/riesgos_mtge/riesgos_mtge_service.py#ADPA-04", "features/roadmap/roadmap_service.py#ADPA-04", "tests/deuda_adpa/riesgos_mtge.txt", "tests/deuda_adpa/roadmap.txt", "tests/test_adpa_dependencias.py#ADPA-04", "features/riesgos_mtge/services/obligaciones_engine.py#ADPA-04", "features/roadmap/ai/roadmap_prompts.py#ADPA-04", "features/roadmap/services/alcance_area_engine.py#ADPA-04", "features/roadmap/services/contexto_generacion.py#ADPA-04", "features/roadmap/services/evidencia_engine.py#ADPA-04", "features/roadmap/services/hallazgo_engine.py#ADPA-04", "features/roadmap/services/informe_estado_engine.py#ADPA-04", "features/roadmap/services/recordatorios_engine.py#ADPA-04", "features/roadmap/services/tarea_asignacion_engine.py#ADPA-04", "app_core/pasillo/diagnostico.py#ADPA-04"]
arbitro = "pytest tests/test_adpa_dependencias.py + suite completa"
rastros = ["¤adpa"]
+++
# ADPA-04 · Retirar deuda lateral ADPA lote 2 (`riesgos_mtge`, `roadmap`) y sellar `DEUDA_LATERAL = 0`

## Entrega
- Crear `app_core/pasillo/rat.py` y completar `app_core/pasillo/organizacion.py#ADPA-04`.
- Redirigir los imports laterales de `riesgos_mtge` y `roadmap` hacia `app_core/pasillo/{diagnostico,organizacion,rat}.py`.
- Vaciar `tests/deuda_adpa/{riesgos_mtge,roadmap}.txt` y sellar `DEUDA_LATERAL == 0` en `tests/test_adpa_dependencias.py#ADPA-04`.

## Pruebas
- `pytest tests/test_adpa_dependencias.py` verifica que las 22 salas tienen 0 aristas laterales (`ImportsCruzados = ∅`).

## Ampliación de propiedad (2026-11-07, Tech Lead)

Los 11 imports laterales están en los motores, no en los `_service.py`. Se amplía la propiedad, por sección `#ADPA-04`, a 9 motores de `riesgos_mtge` y `roadmap`, y a `app_core/pasillo/diagnostico.py#ADPA-04`. Ahí van `politica_evidencia`, `listar_respuestas`, `listar_resultados`, `respuesta_control_desde_fila`, `evaluar_assessment_por_dimension`, `es_resultado_anterior` y los enums. `check_four_eyes`, `SoDViolation` y `RbacError` van en `app_core/pasillo/organizacion.py#ADPA-04`. `app_core/pasillo/rat.py` ya existe, así que se amplía en su sección y no se crea.
