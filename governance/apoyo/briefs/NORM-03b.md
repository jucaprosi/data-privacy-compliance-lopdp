### NORM-03b · pesta-a-impacto-en-el-panel-de-una-resoluci-n-de-norm-02  (tanda 86)

**Contexto.** Sala: `frontend`. Depende de: `NORM-02`, `NORM-03`. Especificaciones: `governance/tareas/NORM-03b.md` y `governance/especificaciones/NORM-03b.md` (manda la especificación).

**Cómo se ejecuta** (esta sesión no tiene el contexto del equipo; todo lo necesario está aquí y en la ficha).

- **Rama:** `tarea/juan-carlos/norm-03b`, creada desde `origin/main` (`git fetch origin` y `git switch -c tarea/juan-carlos/norm-03b origin/main`), en un worktree propio fuera del escritorio.
- **Ficha:** en tu propio PR pon `estado = "en_curso"` en `governance/tareas/NORM-03b.md`. No la marques «hecha».
- **Un PR por ficha.** No lo fusiones: el propietario se lo pasa al CTO, que lo simula y lo fusiona.
- **Entorno:** sin `.env`; la configuración sale de variables de entorno. Las pruebas que abren la base usan el PostgreSQL 16 local (`.\scripts\entorno_local.ps1`) y `exigir_base_de_pruebas()`. Nunca producción ni una base compartida.
- **No edites** `.github/workflows/`, `verificadores/`, `AGENTS.md` ni `.claude/`.
- Archivos nuevos en LF; no cambies el estilo de líneas de los existentes. Pruebas sin `import yaml` (usa `tests/_lector_yaml.py`).
- Antes de pedir revisión: `python scripts/generar_indice_tareas.py --verificar`, `python scripts/verificar_reparto.py` y el árbitro de abajo, con su salida en el PR.

**Objetivo** (en este orden):

1. `NORM-03b` — Pestaña «Impacto» en el panel de una resolución de NORM-02

**UX/UI.** La especificación §4 (pestañas, teclado y visibilidad) y §5 (cinco criterios de Playwright) son el contrato de la interfaz; no inventes textos.

**Rastro ¤**:

- `¤frontend-ide`.

**Escribe** (lista exclusiva):

  - `frontend/src/components/normativa/PanelResolucion.tsx`
  - `frontend/src/components/normativa/CentroVigilancia.tsx`
  - `frontend/tests/normativa_impacto/impacto.spec.ts`
  - `frontend/src/components/layout/menus/index.ts#NORM-02`
  - `frontend/src/components/layout/pantallas/index.tsx#NORM-02`

**No hagas:**

- No escribas fuera de la lista anterior. Si tu ficha tiene secciones `#ID`, escribe solo dentro de tus marcas.
- Cumple el contrato de la especificación; ante una contradicción con el PRD o las invariantes, detente e informa.
- No toques producción ni una base compartida; no despliegues.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `NORM-03b`: Playwright frontend/tests/normativa_impacto/impacto.spec.ts + tsc --noEmit + npm run build; mutación m1.
- `python scripts/generar_indice_tareas.py --verificar` con código 0.
