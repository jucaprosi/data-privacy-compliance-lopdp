### BL-108 · reapertura-por-evidencia-vencida  (tanda 29)

**Contexto.** Sala(s): `auditoria_capa`. Depende de: `CAPA-02` (pendiente), `EVI-02` (pendiente), `RM-21` (pendiente). Especificaciones: `governance/tareas/CAPA-03.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `CAPA-03` — La evidencia vencida reabre el control periódico y produce un hallazgo

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤controles-periodicos`: 2 coincidencias en 2 archivos.
- `¤evidencias-vigencia`: 2 coincidencias en 2 archivos.
- `¤hallazgos`: 3 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `features/auditoria_capa/services/reapertura_engine.py`
  - `features/auditoria_capa/auditoria_capa_service.py#CAPA-03`
  - `tests/test_controles_reapertura.py`
  - `features/auditoria_capa/domain/errores.py#CAPA-03`
  - `app_core/pasillo/auditoria_capa.py#CAPA-03`
  - `app_core/pasillo/evidencias.py#CAPA-03`
  - `app_core/pasillo/roadmap.py#CAPA-03`
  - `app_core/pasillo/notificaciones.py#CAPA-03`
  - `app_core/pasillo/dpo_cockpit.py#CAPA-03`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No guardes vigencias en `auditoria_capa`: se leen de `evidencias`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `CAPA-03`: pytest tests/test_controles_reapertura.py contra un PostgreSQL 16 local en contenedor con lopdp_app + suite completa + vigilantes; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

