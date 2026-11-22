### BOV-02b · montaje-de-los-routers-de-objetos-y-del-orquestador-de-la-b-  (tanda 86)

**Contexto.** Sala: `boveda_cloud`. Depende de: `BOV-01`, `BOV-02`, `BOV-04`, `ORG-22c`. Especificaciones: `governance/tareas/BOV-02b.md` y `governance/especificaciones/BOV-02b.md` (manda la especificación).

**Cómo se ejecuta** (esta sesión no tiene el contexto del equipo; todo lo necesario está aquí y en la ficha).

- **Rama:** `tarea/juan-carlos/bov-02b`, creada desde `origin/main` (`git fetch origin` y `git switch -c tarea/juan-carlos/bov-02b origin/main`), en un worktree propio fuera del escritorio.
- **Ficha:** en tu propio PR pon `estado = "en_curso"` en `governance/tareas/BOV-02b.md`. No la marques «hecha».
- **Un PR por ficha.** No lo fusiones: el propietario se lo pasa al CTO, que lo simula y lo fusiona.
- **Entorno:** sin `.env`; la configuración sale de variables de entorno. Las pruebas que abren la base usan el PostgreSQL 16 local (`.\scripts\entorno_local.ps1`) y `exigir_base_de_pruebas()`. Nunca producción ni una base compartida.
- **No edites** `.github/workflows/`, `verificadores/`, `AGENTS.md` ni `.claude/`.
- Archivos nuevos en LF; no cambies el estilo de líneas de los existentes. Pruebas sin `import yaml` (usa `tests/_lector_yaml.py`).
- Antes de pedir revisión: `python scripts/generar_indice_tareas.py --verificar`, `python scripts/verificar_reparto.py` y el árbitro de abajo, con su salida en el PR.

**Objetivo** (en este orden):

1. `BOV-02b` — Montaje de los routers de objetos y del orquestador de la bóveda por su compuerta

**Rastro ¤**:

- `¤rbac-tenant`, `¤arbitro`.

**Escribe** (lista exclusiva):

  - `features/boveda_cloud/boveda_cloud_service.py#BOV-01`
  - `tests/matriz/BOV-02b.py`
  - `tests/matriz/roles/auditor.py#BOV-02b`
  - `tests/test_bov02b_montaje_routers.py`

**No hagas:**

- No escribas fuera de la lista anterior. Si tu ficha tiene secciones `#ID`, escribe solo dentro de tus marcas.
- Cumple el contrato de la especificación; ante una contradicción con el PRD o las invariantes, detente e informa.
- No toques producción ni una base compartida; no despliegues.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BOV-02b`: pytest tests/test_bov02b_montaje_routers.py tests/test_matriz_permisos.py tests/test_bov04_orquestador_diez_dimensiones.py; mutación m1.
- `python scripts/generar_indice_tareas.py --verificar` con código 0.
