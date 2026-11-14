### BL-180 · sala-videovigilancia-lopdp-camaras-h265-15dias  (tanda 46)

**Contexto.** Sala(s): `videovigilancia`. Depende de: `ADPA-06`, `ADPA-07`, `BOV-01`, `MARCA-01`. Especificaciones: `governance/tareas/CCTV-01.md`, `governance/especificaciones/CCTV-01.md`.

**Objetivo** (en este orden):

1. `CCTV-01` — Sala Videovigilancia LOPDP: inventario de cámaras/NVR, auditoría de perfil técnico (H.265, eventos, sin audio, máscaras) y retención de 15 días

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤videovigilancia-cctv`: registrado en `VPA_MAP.md`.
- `¤boveda-cloud`: registrado en `VPA_MAP.md`.
- `¤rat`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `alembic/versions/20260501_02_cctv01_camaras_y_politicas.py`
  - `features/videovigilancia/__init__.py`
  - `features/videovigilancia/models.py`
  - `features/videovigilancia/schemas.py`
  - `features/videovigilancia/videovigilancia_service.py#CCTV-01`
  - `features/videovigilancia/domain/__init__.py`
  - `features/videovigilancia/domain/errores.py#CCTV-01`
  - `features/videovigilancia/routes/__init__.py`
  - `features/videovigilancia/routes/videovigilancia_routes.py`
  - `app_core/pasillo/videovigilancia.py#CCTV-01`
  - `app_core/pasillo/rat.py#CCTV-01`
  - `main.py#CCTV-01`
  - `frontend/src/components/layout/menus/index.ts#CCTV-01`
  - `frontend/src/components/layout/pantallas/index.tsx#CCTV-01`
  - `frontend/src/components/layout/pantallas/CCTV-01.tsx`
  - `tests/test_cctv01_inventario_y_perfil_camaras.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `CCTV-01`: pytest tests/test_cctv01_inventario_y_perfil_camaras.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

