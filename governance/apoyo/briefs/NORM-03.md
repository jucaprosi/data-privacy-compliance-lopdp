### BL-189 · impacto-normativo-gemini-hitl-y-cache  (tanda 46)

**Contexto.** Sala(s): `inteligencia_normativa, ai_copilot`. Depende de: `NORM-01`, `VTX-01`. Especificaciones: `governance/tareas/NORM-03.md`, `governance/especificaciones/NORM-03.md`.

**Objetivo** (en este orden):

1. `NORM-03` — Análisis de impacto de una resolución con Gemini, validado por persona, y regeneración de la caché de contexto

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤inteligencia-normativa`: registrado en `VPA_MAP.md`.
- `¤copiloto-ia`: registrado en `VPA_MAP.md`.
- `¤vertex-cache`: registrado en `VPA_MAP.md`.
- `¤dpo-independencia`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261104_norm03_analisis_impacto.py`
  - `features/inteligencia_normativa/inteligencia_normativa_service.py#NORM-03`
  - `features/inteligencia_normativa/domain/errores.py#NORM-03`
  - `features/inteligencia_normativa/services/impacto.py`
  - `features/inteligencia_normativa/services/extraccion.py`
  - `features/ai_copilot/ai_copilot_service.py#NORM-03`
  - `app_core/pasillo/ai_copilot.py#NORM-03`
  - `app_core/pasillo/regulacion_rag.py#NORM-03`
  - `api/routers/inteligencia_normativa_impacto.py`
  - `tests/test_norm03_impacto_hitl.py`
  - `frontend/src/components/normativa_impacto/**`
  - `frontend/tests/normativa_impacto/**`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `NORM-03`: pytest tests/test_norm03_impacto_hitl.py contra un PostgreSQL 16 local en contenedor + suite completa + Playwright de frontend/tests/normativa_impacto + tsc --noEmit + npm run build
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

