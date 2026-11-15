### BL-140 · solicitudes-de-titulares-verificacin-de-identida  (tanda 59)

**Contexto.** Sala(s): `derechos_arco`, `frontend`. Depende de: `EVI-02` (pendiente), `FE-22` (pendiente), `DER-06b`. Especificaciones: `governance/tareas/DER-01.md`, `governance/especificaciones/DER-01.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `DER-01` — Solicitudes de titulares: verificación de identidad, modelos de respuesta y la respuesta como evidencia

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤evidencias`: 35 coincidencias en 13 archivos.
- `¤rbac-tenant`: 103 coincidencias en 66 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/der01_derechos_respuestas.py`
  - `features/derechos_arco/services/respuestas_engine.py`
  - `features/derechos_arco/derechos_arco_service.py#DER-01`
  - `api/routers/derechos_respuestas.py`
  - `tests/test_derechos_respuestas.py`
  - `tests/matriz/DER-01.py`
  - `frontend/src/components/derechos/**`
  - `frontend/src/lib/derechos/respuestas.ts`
  - `frontend/src/types/arco.ts`
  - `frontend/tests/derechos/respuestas.spec.ts`
  - `features/derechos_arco/domain/errores.py#DER-01`
  - `app_core/pasillo/derechos_arco.py#DER-01`
  - `app_core/pasillo/evidencias.py#DER-01`
  - `app_core/pasillo/firma_electronica.py#DER-01`
  - `app_core/pasillo/notificaciones.py#DER-01`
  - `app_core/pasillo/dpo_cockpit.py#DER-01`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/DER-01.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni una base compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DER-01`: pytest tests/test_derechos_respuestas.py contra un PostgreSQL 16 local en contenedor (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/derechos/respuestas.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada; las pruebas de la evidencia obligatoria (test_contestar_sin_evidencia_422, test_hash_del_cliente_rechazado, test_check_contestada_exige_hash y test_migracion_der01_aborta_con_contestadas_sin_hash) cada una con su mutación
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

