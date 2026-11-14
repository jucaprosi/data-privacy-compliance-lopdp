### BL-178 · boveda-dual-gcs-short-ttl-vs-long-retention-worm  (tanda 46)

**Contexto.** Sala(s): `boveda_cloud`. Depende de: `BOV-01`. Especificaciones: `governance/tareas/BOV-02.md`, `governance/especificaciones/BOV-02.md`.

**Objetivo** (en este orden):

1. `BOV-02` — Bóveda Dual en Google Cloud Storage (short-ttl Standard vs long-retention Autoclass WORM) e ingesta Direct-to-GCS

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤boveda-cloud`: registrado en `VPA_MAP.md`.
- `¤conservacion`: registrado en `VPA_MAP.md`.
- `¤evidencias`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/boveda_cloud/services/__init__.py`
  - `features/boveda_cloud/services/gcs_dual_vault_engine.py`
  - `features/boveda_cloud/boveda_cloud_service.py#BOV-02`
  - `features/boveda_cloud/domain/errores.py#BOV-02`
  - `features/boveda_cloud/routes/boveda_objetos_routes.py`
  - `app_core/pasillo/boveda_cloud.py#BOV-02`
  - `tests/test_bov02_gcs_dual_vault.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BOV-02`: pytest tests/test_bov02_gcs_dual_vault.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

