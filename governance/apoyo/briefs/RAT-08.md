### BL-337 · rat-area-responsable-como-referencia-al-area  (tanda 77)

**Contexto.** Sala: `rat, frontend`. Depende de: nada abierto. Especificaciones: `governance/tareas/RAT-08.md`.

**Objetivo** (en este orden):

1. `RAT-08` — Área responsable del tratamiento como referencia al área de la organización

**Rastro ¤**:

- `¤rat`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `alembic/versions/rat08_area_id.py`
  - `tests/test_rat08_area_id.py`
  - `frontend/src/types/rat_area.ts`
  - `features/rat/domain/models.py`
  - `features/rat/services/rat_engine.py`
  - `api/routers/rat.py`
  - `frontend/src/components/modules/RatModule.tsx`
  - `features/rat/rat_service.py#RAT-08`
  - `app_core/pasillo/organizacion.py#RAT-08`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- No uses la base ni el proyecto de producción.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `RAT-08`: pytest tests/test_rat08_area_id.py contra PostgreSQL 16 local + alembic heads con una sola cabeza + tsc --noEmit; mutaciones m1 a m3
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.
