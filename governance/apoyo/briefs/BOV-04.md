### BOV-04 · orquestador-comercial-diez-dimensiones-y-boveda-cloud  (tanda 48)

**Contexto.** Sala(s): `boveda_cloud`. Depende de: `BOV-03`, `CCTV-02`, `GOVW-01`, `GOCA-01`, `DLP-01`, `VTX-01`. Especificaciones: `governance/tareas/BOV-04.md`, `governance/especificaciones/BOV-04.md`.

**Cómo se ejecuta** (esta sesión no tiene el contexto del equipo; todo lo necesario está aquí y en la ficha).

- **Rama:** `tarea/juan-carlos/bov-04`, creada desde `origin/main` (`git fetch origin` y `git switch -c tarea/juan-carlos/bov-04 origin/main`), en un worktree propio fuera del escritorio.
- **Ficha:** en tu propio PR pon `estado = "en_curso"` en `governance/tareas/BOV-04.md`. No la marques «hecha».
- **Un PR por ficha.** No lo fusiones: el propietario se lo pasa al CTO, que lo simula y lo fusiona.
- **Entorno:** sin `.env`; la configuración sale de variables de entorno. Las pruebas que abren la base usan el PostgreSQL 16 local (`.\scripts\entorno_local.ps1`) y `exigir_base_de_pruebas()`. Nunca producción ni una base compartida.
- **No edites** `.github/workflows/`, `verificadores/`, `AGENTS.md` ni `.claude/`.
- Archivos nuevos en LF; no cambies el estilo de líneas de los existentes. Pruebas sin `import yaml` (usa `tests/_lector_yaml.py`).
- Antes de pedir revisión: `python scripts/generar_indice_tareas.py --verificar`, `python scripts/verificar_reparto.py` y el árbitro de abajo, con su salida en el PR.

**Objetivo** (en este orden):

1. `BOV-04` — Orquestador Comercial de las 10 Dimensiones y Bóveda Cloud: centro de mando de automatizaciones, retenciones, actas SHA-256 y telemetría de paquete

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤boveda-cloud`: registrado en `VPA_MAP.md`.
- `¤videovigilancia-cctv`: registrado en `VPA_MAP.md`.
- `¤dpo-cockpit`: registrado en `VPA_MAP.md`.
- `¤conservacion`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/boveda_cloud/services/orquestador_diez_dimensiones.py`
  - `features/boveda_cloud/boveda_cloud_service.py#BOV-04`
  - `features/boveda_cloud/domain/errores.py#BOV-04`
  - `features/boveda_cloud/routes/orquestador_routes.py`
  - `app_core/pasillo/boveda_cloud.py#BOV-04`
  - `app_core/pasillo/dpo_cockpit.py#BOV-04`
  - `frontend/src/components/layout/menus/index.ts#BOV-04`
  - `frontend/src/components/layout/pantallas/index.tsx#BOV-04`
  - `frontend/src/components/layout/pantallas/BOV-04.tsx`
  - `tests/test_bov04_orquestador_diez_dimensiones.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BOV-04`: pytest tests/test_bov04_orquestador_diez_dimensiones.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

