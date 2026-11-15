### BL-145 · portal-pblico-de-solicitudes-de-titulares-por-or  (tanda 60)

**Contexto.** Sala(s): `derechos_arco`, `frontend`. Depende de: `DER-01` (pendiente), `SEC-12` (pendiente), `DER-06b`. Especificaciones: `governance/tareas/DER-02.md`, `governance/especificaciones/DER-02.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `DER-02` — Portal público de solicitudes de titulares por organización, con enlace de seguimiento

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤seguridad`: 78 coincidencias en 47 archivos.
- `¤rbac-tenant`: 103 coincidencias en 66 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261105_derechos_portal.py`
  - `features/derechos_arco/services/portal_engine.py`
  - `features/derechos_arco/derechos_arco_service.py#DER-02`
  - `api/routers/publico_derechos.py`
  - `tests/test_derechos_portal.py`
  - `frontend/src/app/solicitud/**`
  - `frontend/tests/derechos/portal.spec.ts`
  - `features/derechos_arco/domain/errores.py#DER-02`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/DER-02.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni una base compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DER-02`: pytest tests/test_derechos_portal.py contra un PostgreSQL 16 local en contenedor + suite completa + Playwright de frontend/tests/derechos/portal.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada; cumple el diseño de SEC-12
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

