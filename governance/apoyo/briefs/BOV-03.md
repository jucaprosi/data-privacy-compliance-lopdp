### BL-181 · carril-forense-dual-sha256-original-y-preview-webp  (tanda 47)

**Contexto.** Sala(s): `boveda_cloud`. Depende de: `BOV-02`. Especificaciones: `governance/tareas/BOV-03.md`, `governance/especificaciones/BOV-03.md`.

**Objetivo** (en este orden):

1. `BOV-03` — Carril Forense Dual: custodia del original intacto SHA-256 y derivados de previsualización WebP/AVIF/WebM

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤boveda-cloud`: registrado en `VPA_MAP.md`.
- `¤evidencias`: registrado en `VPA_MAP.md`.
- `¤adpa`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/boveda_cloud/services/forensic_preview_engine.py`
  - `features/boveda_cloud/boveda_cloud_service.py#BOV-03`
  - `features/boveda_cloud/domain/errores.py#BOV-03`
  - `app_core/pasillo/boveda_cloud.py#BOV-03`
  - `frontend/src/components/layout/pantallas/BOV-03.tsx`
  - `frontend/src/components/layout/pantallas/index.tsx#BOV-03`
  - `tests/test_bov03_forensic_preview.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BOV-03`: pytest tests/test_bov03_forensic_preview.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

