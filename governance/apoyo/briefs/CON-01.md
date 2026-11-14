### BL-172 · sala-conservacion-y-bloqueo-politicas-retencion  (tanda 31)

**Contexto.** Sala(s): `conservacion`. Depende de: `ADPA-07`, `ADPA-09`, `RAT-07`, `MARCA-01`. Especificaciones: `governance/tareas/CON-01.md`.

**Objetivo** (en este orden):

1. `CON-01` — Sala Conservación y Bloqueo: políticas de retención, purga/anonimización e integración con RAT y DPO Cockpit

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 407 coincidencias en 96 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20260429_01_con01_politicas_conservacion.py`
  - `features/conservacion/models.py`
  - `features/conservacion/schemas.py`
  - `features/conservacion/conservacion_service.py#CON-01`
  - `features/conservacion/domain/errores.py#CON-01`
  - `features/conservacion/routes/__init__.py`
  - `features/conservacion/routes/conservacion_routes.py`
  - `app_core/pasillo/conservacion.py#CON-01`
  - `app_core/pasillo/rat.py#CON-01`
  - `app_core/pasillo/dpo_cockpit.py#CON-01`
  - `main.py#CON-01`
  - `frontend/src/components/layout/menus/index.ts#CON-01`
  - `frontend/src/components/layout/pantallas/index.tsx#CON-01`
  - `frontend/src/components/layout/pantallas/CON-01.tsx`
  - `tests/test_con01_conservacion.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni una base compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `CON-01`: pytest tests/test_con01_conservacion.py contra un PostgreSQL 16 local en contenedor con lopdp_app + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

