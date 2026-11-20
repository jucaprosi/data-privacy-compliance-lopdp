### DEMO-05c · purga-demo-politicas-por-rol  (tanda 1)

**Contexto.** Sala: `demo`. Depende de: nada abierto. Especificaciones: `governance/tareas/DEMO-05c.md` y `governance/especificaciones/DEMO-05c.md`.

**Cómo se ejecuta** (esta sesión no tiene el contexto del equipo; todo lo necesario está aquí y en la ficha).

- **Rama:** `tarea/juan-carlos/demo-05c`, creada desde `origin/main` (`git fetch origin` y `git switch -c tarea/juan-carlos/demo-05c origin/main`), en un worktree propio fuera del escritorio.
- **Ficha:** en tu propio PR pon `estado = "en_curso"` en `governance/tareas/DEMO-05c.md`. No la marques «hecha».
- **Un PR por ficha.** No lo fusiones: el propietario se lo pasa al CTO, que lo simula y lo fusiona.
- **Entorno:** sin `.env`; la configuración sale de variables de entorno. Las pruebas que abren la base usan el PostgreSQL 16 local (`.\scripts\entorno_local.ps1`) y `exigir_base_de_pruebas()`. Nunca producción ni una base compartida.
- **No edites** `.github/workflows/`, `verificadores/`, `AGENTS.md` ni `.claude/`.
- Archivos nuevos en LF; no cambies el estilo de líneas de los existentes. Pruebas sin `import yaml` (usa `tests/_lector_yaml.py`).
- Antes de pedir revisión: `python scripts/generar_indice_tareas.py --verificar`, `python scripts/verificar_reparto.py` y el árbitro de abajo, con su salida en el PR.

**Objetivo** (en este orden):

1. `DEMO-05c` — Purga de la demo con políticas explícitas por rol, sin BYPASSRLS, y guardia que falla cerrada si falta alguna

**Rastro ¤**:

- `¤demo`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `jobs/purga_demo/politicas_purga.sql`
  - `jobs/purga_demo/guardias.py`
  - `jobs/purga_demo/__main__.py`
  - `governance/operaciones/BRIEF_PROPIETARIO_DEMO05.md`
  - `tests/test_demo05c_politicas_purga.py`
  - `jobs/purga_demo/purga.py`

**No hagas:**

- No escribas fuera de la lista anterior.
- Cumple el contrato de `governance/especificaciones/DEMO-05c.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No toques producción ni una base compartida; el SQL se valida solo en la PostgreSQL efímera.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DEMO-05c`: pytest tests/test_demo05c_politicas_purga.py con TEST_DATABASE_URL de PostgreSQL 16; mutaciones m1 a m5.
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.
