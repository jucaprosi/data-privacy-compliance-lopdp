+++
id = "ADPA-02"
titulo = "Reubicar ErrorNegocio en app_core/errors.py y prohibir imports features -> api"
ola = "C"
estado = "hecha"
sala = "auditoria_capa, biblioteca, dpo_cockpit, organizacion, rat, roadmap"
depende_de = ["ADPA-01", "BIB-112", "CAPA-02", "DIAG-08", "DPO-02", "ORG-13", "ORG-14", "ORG-16", "RAT-06", "RM-21", "RM-24"]
propiedad = [
  "app_core/errors.py#ADPA-02",
  "api/errores.py#ADPA-02",
  "features/auditoria_capa/services/controles_engine.py#ADPA-02",
  "features/biblioteca/domain/editorial.py#ADPA-02",
  "features/biblioteca/domain/plantillas_md.py#ADPA-02",
  "features/biblioteca/services/autorizacion.py#ADPA-02",
  "features/biblioteca/services/editorial.py#ADPA-02",
  "features/biblioteca/services/importacion.py#ADPA-02",
  "features/biblioteca/services/plantillas_md.py#ADPA-02",
  "features/dpo_cockpit/services/informe_anual_engine.py#ADPA-02",
  "features/dpo_cockpit/services/inscripcion_engine.py#ADPA-02",
  "features/organizacion/services/alta_engine.py#ADPA-02",
  "features/organizacion/services/configuracion_engine.py#ADPA-02",
  "features/organizacion/services/datos_documentales_engine.py#ADPA-02",
  "features/organizacion/services/excepcion_sod_engine.py#ADPA-02",
  "features/organizacion/services/invitaciones_personas_engine.py#ADPA-02",
  "features/organizacion/services/regla_tamano_engine.py#ADPA-02",
  "features/organizacion/services/roles_engine.py#ADPA-02",
  "features/organizacion/services/solicitud_responsable_engine.py#ADPA-02",
  "features/rat/rat_service.py#ADPA-02",
  "features/rat/services/exportacion_engine.py#ADPA-02",
  "features/roadmap/services/cierre_verificado_engine.py#ADPA-02",
  "features/roadmap/services/hallazgo_engine.py#ADPA-02",
  "features/roadmap/services/tarea_asignacion_engine.py#ADPA-02",
  "features/roadmap/services/tarea_edicion_engine.py#ADPA-02",
  "tests/test_adpa_dependencias.py#ADPA-02"
]
arbitro = "pytest tests/test_adpa_dependencias.py + suite completa"
rastros = ["¤adpa", "¤errores"]
+++
# ADPA-02 · Reubicar `ErrorNegocio` en `app_core/errors.py` y prohibir imports `features/` -> `api/`

## Entrega
- Definir `ErrorNegocio` canónicamente en `app_core/errors.py` (`#ADPA-02`) y reexportarlo en `api/errores.py` (`#ADPA-02`) conservando el handler HTTP de FastAPI.
- Migrar los 21 archivos de `features/` que importan `from api.errores import ErrorNegocio` a `from app_core.errors import ErrorNegocio` para cumplir la Regla 3 del PRD §7.1 (`api/ -> features/<sala>/ -> app_core/ -> db/`).
- Añadir `test_ninguna_sala_importa_capa_api` en `tests/test_adpa_dependencias.py#ADPA-02`.

## Pruebas
- `pytest tests/test_adpa_dependencias.py` falla si cualquier módulo en `features/` importa de `api` o `api.*`.
