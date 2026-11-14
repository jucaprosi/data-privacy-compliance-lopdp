### BL-153 · cuestionario-de-garantas-del-encargado-por-porta  (tanda 32)

**Contexto.** Sala(s): `terceros`, `frontend`. Depende de: `TER-01` (pendiente), `SEC-12` (pendiente), `FE-23` (pendiente). Especificaciones: `governance/tareas/TER-02.md`, `governance/especificaciones/TER-02.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `TER-02` — Cuestionario de garantías del encargado por portal externo, con revisión e informe

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤seguridad`: 78 coincidencias en 47 archivos.
- `¤evidencias`: 35 coincidencias en 13 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261107_terceros_cuestionario.py`
  - `features/terceros/services/cuestionario_engine.py`
  - `features/terceros/terceros_service.py#TER-02`
  - `api/routers/publico_terceros.py`
  - `api/routers/terceros_cuestionario.py`
  - `tests/test_terceros_cuestionario.py`
  - `tests/matriz/TER-02.py`
  - `frontend/src/app/proveedor/**`
  - `frontend/src/components/terceros/**`
  - `frontend/tests/terceros/cuestionario.spec.ts`
  - `features/transferencias/domain/errores.py#TER-02`
  - `app_core/pasillo/transferencias.py#TER-02`
  - `app_core/pasillo/terceros.py#TER-02`
  - `app_core/pasillo/rat.py#TER-02`
  - `app_core/pasillo/dpo_cockpit.py#TER-02`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/TER-02.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni una base compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `TER-02`: pytest tests/test_terceros_cuestionario.py contra un PostgreSQL 16 local en contenedor + suite completa + Playwright de frontend/tests/terceros/cuestionario.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada; cumple el diseño de SEC-12
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

