### BL-182 · congelamiento-forense-hold-legal-cctv-y-acta-quincenal  (tanda 47)

**Contexto.** Sala(s): `videovigilancia`. Depende de: `CCTV-01`, `BOV-02`, `CON-01`. Especificaciones: `governance/tareas/CCTV-02.md`, `governance/especificaciones/CCTV-02.md`.

**Objetivo** (en este orden):

1. `CCTV-02` — Congelamiento Forense (Hold Legal) de clips de videovigilancia por incidente o derecho ARCOP y actas quincenales de destrucción SHA-256

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤videovigilancia-cctv`: registrado en `VPA_MAP.md`.
- `¤incidentes`: registrado en `VPA_MAP.md`.
- `¤derechos`: registrado en `VPA_MAP.md`.
- `¤conservacion`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/videovigilancia/services/__init__.py`
  - `features/videovigilancia/services/cctv_legal_hold_engine.py`
  - `features/videovigilancia/videovigilancia_service.py#CCTV-02`
  - `features/videovigilancia/domain/errores.py#CCTV-02`
  - `features/videovigilancia/routes/cctv_hold_routes.py`
  - `app_core/pasillo/videovigilancia.py#CCTV-02`
  - `app_core/pasillo/incidentes.py#CCTV-02`
  - `app_core/pasillo/derechos_arco.py#CCTV-02`
  - `frontend/src/components/layout/pantallas/CCTV-02.tsx`
  - `frontend/src/components/layout/pantallas/index.tsx#CCTV-02`
  - `tests/test_cctv02_legal_hold_y_acta_purga.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `CCTV-02`: pytest tests/test_cctv02_legal_hold_y_acta_purga.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

