### DEMO-05d · purga-de-la-demo-frente-a-los-triggers-de-inmutabilidad  (tanda 84)

**Contexto.** Sala: `demo`. Depende de: `DEMO-05`, `DEMO-05b`, `DEMO-05c`, `SEC-20`. Especificaciones: `governance/tareas/DEMO-05d.md` y `governance/especificaciones/DEMO-05d.md`. No se lanza hasta que DEMO-05c esté fusionada.

**Cómo se ejecuta** (esta sesión no tiene el contexto del equipo; todo lo necesario está aquí y en la ficha).

- **Rama:** `tarea/juan-carlos/demo-05d`, creada desde `origin/main` (`git fetch origin` y `git switch -c tarea/juan-carlos/demo-05d origin/main`), en un worktree propio fuera del escritorio.
- **Ficha:** en tu propio PR pon `estado = "en_curso"` en `governance/tareas/DEMO-05d.md`. No la marques «hecha».
- **Un PR por ficha.** No lo fusiones: el propietario se lo pasa al CTO, que lo simula y lo fusiona.
- **Entorno:** sin `.env`; la configuración sale de variables de entorno. Las pruebas que abren la base usan el PostgreSQL 16 local (`.\scripts\entorno_local.ps1`) y `exigir_base_de_pruebas()`. Nunca producción ni una base compartida.
- **No edites** `.github/workflows/`, `verificadores/`, `AGENTS.md` ni `.claude/`.
- Archivos nuevos en LF; no cambies el estilo de líneas de los existentes. Pruebas sin `import yaml` (usa `tests/_lector_yaml.py`).
- Antes de pedir revisión: `python scripts/generar_indice_tareas.py --verificar`, `python scripts/verificar_reparto.py` y el árbitro de abajo, con su salida en el PR.

**Objetivo** (en este orden):

1. `DEMO-05d` — Purga de la demo frente a los triggers de inmutabilidad de biblioteca y consultas al DPO

**Rastro ¤**:

- `¤demo`.

**Escribe** (lista exclusiva):

  - `jobs/purga_demo/politicas_purga.sql`
  - `jobs/purga_demo/purga.py`
  - `jobs/purga_demo/guardias.py`
  - `jobs/purga_demo/__main__.py`
  - `governance/operaciones/BRIEF_PROPIETARIO_DEMO05.md`
  - `tests/test_demo05d_purga_inmutables.py`

**No hagas:**

- No escribas fuera de la lista anterior.
- Cumple el contrato de `governance/especificaciones/DEMO-05d.md`; ante una contradicción con el PRD o las invariantes, detente e informa. La ficha cita el invariante 63 de EVYDENTIA y no toca la inmutabilidad de producción.
- No toques producción ni una base compartida; no despliegues.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DEMO-05d`: pytest tests/test_demo05d_purga_inmutables.py con TEST_DATABASE_URL de PostgreSQL 16; mutaciones m1 a m6.
- `python scripts/generar_indice_tareas.py --verificar` con código 0.
