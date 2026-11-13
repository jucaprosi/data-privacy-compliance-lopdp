+++
id = "RAT-08"
titulo = "Área responsable del tratamiento como referencia al área de la organización"
ola = "backlog"
estado = "pendiente"
sala = "rat, frontend"
depende_de = ["RAT-01", "RAT-05", "RAT-02", "RAT-06", "API-01", "RAT-07"]
propiedad = ["alembic/versions/rat08_area_id.py", "tests/test_rat08_area_id.py", "frontend/src/types/rat_area.ts", "features/rat/domain/models.py", "features/rat/services/rat_engine.py", "api/routers/rat.py", "frontend/src/components/modules/RatModule.tsx", "features/rat/rat_service.py#RAT-08", "app_core/pasillo/organizacion.py#RAT-08"]
crea = ["alembic/versions/rat08_area_id.py", "tests/test_rat08_area_id.py", "frontend/src/types/rat_area.ts"]
arbitro = "pytest tests/test_rat08_area_id.py contra PostgreSQL 16 local + alembic heads con una sola cabeza + tsc --noEmit; mutaciones m1 a m3"
rastros = ["¤rat"]
+++

# RAT-08 · Área responsable del tratamiento como referencia al área de la organización

Decisión del CTO (2026-11-13), en backlog y sin urgencia. Hoy `area_responsable` del RAT es texto libre (`features/rat/domain/models.py:53`, `str = ""`), así que no se puede derivar de forma fiable qué personas tienen tratamientos asignados.

## Entrega
- `rat_actividades.area_id` como FK a las áreas de organización (por su compuerta), con migración de datos que empareja por nombre (en minúsculas y sin espacios en los extremos) y deja `NULL` lo que no case; `area_responsable` se conserva como texto mientras haya filas sin emparejar.
- Migración sin fecha, con FUSION_ALEMBIC.
- Cuando exista, FOR-01 o una ficha hija puede afinar el denominador de la cobertura por área.

## Mutaciones
m1 emparejar sin normalizar mayúsculas → falla la prueba de emparejado; m2 inventar un área para un texto que no casa → falla; m3 borrar `area_responsable` con filas sin emparejar → falla.

**Medición del Arquitecto (2026-11-13).** FK compuesta `(area_id, tenant_id)` a las áreas de organización; `area_responsable` se conserva. La migración empareja por `lower(trim)` solo si la coincidencia es única e imprime los recuentos (emparejadas, sin emparejar, ambiguas). Se ordena después de RAT-07, que toca los mismos archivos del RAT.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#RAT-08` (ADR 0001).
