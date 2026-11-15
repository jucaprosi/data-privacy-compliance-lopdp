### BL-154 · aceptacin-simple-con-acuse-nombre-correo-fecha-i  (tanda 32)

**Contexto.** Sala(s): `firma_electronica`, `frontend`. Depende de: `FIRMA-01`, `EVI-02`, `BIB-107`, `EVI-04`. Especificaciones: `governance/tareas/FIRMA-02.md`, `governance/especificaciones/FIRMA-02.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `FIRMA-02` — Aceptación simple con acuse (nombre, correo, fecha, IP y sello hash) y verificación de documentos por hash

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤firma-electronica`: 9 coincidencias en 7 archivos.
- `¤evidencias`: 35 coincidencias en 13 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261103_aceptaciones.py`
  - `features/firma_electronica/domain/aceptacion.py`
  - `features/firma_electronica/services/aceptacion_engine.py`
  - `features/firma_electronica/firma_electronica_service.py#FIRMA-02`
  - `api/routers/firma_aceptaciones.py`
  - `api/routers/publico_aceptacion.py`
  - `tests/test_firma_aceptaciones.py`
  - `tests/matriz/FIRMA-02.py`
  - `frontend/src/app/aceptar/**`
  - `frontend/src/components/firma/**`
  - `frontend/src/lib/firma/aceptaciones.ts`
  - `frontend/tests/firma/aceptacion.spec.ts`
  - `features/firma_electronica/domain/errores.py#FIRMA-02`
  - `app_core/pasillo/firma_electronica.py#FIRMA-02`
  - `app_core/pasillo/evidencias.py#FIRMA-02`
  - `app_core/pasillo/rat.py#FIRMA-02`
  - `app_core/pasillo/riesgos_mtge.py#FIRMA-02`
  - `app_core/pasillo/derechos_arco.py#FIRMA-02`
  - `frontend/src/components/layout/menus/index.ts#FIRMA-02`
  - `frontend/src/components/layout/menus/FIRMA-02.ts`
  - `frontend/src/components/layout/pantallas/FIRMA-02.tsx`
  - `frontend/src/components/layout/pantallas/index.tsx#FIRMA-02`
  - `frontend/tests/biblioteca/acceso.spec.ts#FIRMA-02`
  - `features/biblioteca/biblioteca_service.py#FIRMA-02`
  - `app_core/pasillo/biblioteca.py#FIRMA-02`
  - `app_core/pasillo/organizacion.py#FIRMA-02`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/FIRMA-02.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni una base compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `FIRMA-02`: pytest tests/test_firma_aceptaciones.py contra un PostgreSQL 16 local en contenedor (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/firma/aceptacion.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

