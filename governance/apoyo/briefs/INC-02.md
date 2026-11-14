### BL-137 · asistente-de-vulneracin-en-ocho-secciones-con-de  (tanda 29)

**Contexto.** Sala(s): `incidentes`, `frontend`. Depende de: `INC-01`, `FE-23` (pendiente), `RM-21` (pendiente), `EVI-02` (pendiente), `EVI-04` (pendiente). Especificaciones: `governance/tareas/INC-02.md`, `governance/especificaciones/INC-02.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `INC-02` — Asistente de vulneración en ocho secciones con decisión de notificar e informes de la norma técnica

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤incidentes`: 15 coincidencias en 13 archivos.
- `¤hallazgos`: 5 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/inc02_incidentes_asistente.py`
  - `features/incidentes/domain/vulneracion.py`
  - `features/incidentes/services/asistente_engine.py`
  - `features/incidentes/services/informes_engine.py`
  - `features/incidentes/incidentes_service.py#INC-02`
  - `api/routers/incidentes_asistente.py`
  - `tests/test_incidentes_asistente.py`
  - `tests/matriz/INC-02.py`
  - `frontend/src/components/incidentes/**`
  - `frontend/src/lib/incidentes/asistente.ts`
  - `frontend/tests/incidentes/asistente.spec.ts`
  - `frontend/src/components/layout/menus/INC-02.ts`
  - `frontend/src/components/layout/pantallas/INC-02.tsx`
  - `features/incidentes/domain/errores.py#INC-02`
  - `app_core/pasillo/incidentes.py#INC-02`
  - `app_core/pasillo/evidencias.py#INC-02`
  - `app_core/pasillo/notificaciones.py#INC-02`
  - `app_core/pasillo/dpo_cockpit.py#INC-02`
  - `frontend/src/components/layout/menus/index.ts#INC-02`
  - `frontend/src/components/layout/pantallas/index.tsx#INC-02`
  - `tests/matriz/roles/auditor.py#INC-02`
  - `app_core/pasillo/roadmap.py#INC-02`
  - `features/incidentes/incidentes_service.py#INC-03`
  - `tests/test_seleccionar_pruebas.py`
  - `tests/test_inc03_estado_incidente.py`
  - `tests/matriz/roles/auditor.py#INC-02`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/INC-02.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni una base compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `INC-02`: pytest tests/test_incidentes_asistente.py contra un PostgreSQL 16 local en contenedor (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/incidentes/asistente.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

