### LEG-06 · licencia-propietaria-y-aviso-de-derechos-de-autor-en-todo-ar  (tanda 92)

**Contexto.** Sala: `gobernanza`. Depende de: `CI-19`, `CI-22`, `CI-23`, `CI-25`, `CI-26`, `CI-29`, `CI-31`, `CI-36`, `GCP-07`, `PRD-01`, `PRD-03`, `QA-11`, `RET-05`, `RET-09`. Especificaciones: `governance/tareas/LEG-06.md` y `governance/especificaciones/LEG-06.md` (manda la especificación).

**Orden.** Es el último bloque de su tanda y no puede haber otra ficha en `en_curso` (R6). CI-36 (tanda 91) debe estar cerrada antes.

**Cómo se ejecuta** (esta sesión no tiene el contexto del equipo; todo lo necesario está aquí y en la ficha).

- **Rama:** `tarea/juan-carlos/leg-06`, creada desde `origin/main` (`git fetch origin` y `git switch -c tarea/juan-carlos/leg-06 origin/main`), en un worktree propio fuera del escritorio.
- **Ficha:** en tu propio PR pon `estado = "en_curso"` en `governance/tareas/LEG-06.md`. No la marques «hecha».
- **Un PR por ficha.** No lo fusiones: el propietario se lo pasa al CTO, que lo simula y lo fusiona.
- **Entorno:** sin `.env`; la configuración sale de variables de entorno. Las pruebas que abren la base usan el PostgreSQL 16 local (`.\scripts\entorno_local.ps1`) y `exigir_base_de_pruebas()`. Nunca producción ni una base compartida.
- **No edites** `.github/workflows/`, `verificadores/`, `AGENTS.md` ni `.claude/`.
- Archivos nuevos en LF; no cambies el estilo de líneas de los existentes. Pruebas sin `import yaml` (usa `tests/_lector_yaml.py`).
- Antes de pedir revisión: `python scripts/generar_indice_tareas.py --verificar`, `python scripts/verificar_reparto.py` y el árbitro de abajo, con su salida en el PR.

**Objetivo** (en este orden):

1. `LEG-06` — Licencia propietaria y aviso de derechos de autor en todo archivo de código versionado

- **LICENSE** es copia literal de `jucaprosi/evydentia@23b1d32:LICENSE` (`gh api repos/jucaprosi/evydentia/contents/LICENSE`) o de `C:/Users/Juan Carlos/respaldo-evydentia/LICENSE`. Su SHA-256 debe ser `f814709c25412c5863eec4c284303f790c04b6063356907468f964b73ee3a7db`. No se lo pidas al propietario: la fuente está fijada en la especificación.
- **R5 (aviso transversal):** además de su propiedad, añade la línea de aviso a los archivos que lista la especificación. Cada uno lleva solo esa línea. `verificar_alcance_pr.py` admite el diff solo si cumple (a), (b) y (c) de R5.

**Rastro ¤**:

- `¤ip`, `¤arbitro`.

**Escribe** (lista exclusiva):

  - `LICENSE`
  - `frontend/package.json`
  - `scripts/poner_aviso_de_autor.py`
  - `scripts/verificar_alcance_pr.py`
  - `tests/test_verificar_alcance_pr.py`
  - `tests/test_leg06_aviso_de_autor.py`

**No hagas:**

- No escribas fuera de la lista anterior, salvo lo que la especificación pide por su regla transversal.
- Cumple el contrato de la especificación; ante una contradicción con el PRD o las invariantes, detente e informa.
- No toques producción ni una base compartida; no despliegues.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `LEG-06`: pytest tests/test_leg06_aviso_de_autor.py tests/test_verificar_alcance_pr.py; python -m compileall -q .; npx tsc --noEmit y npm run lint en frontend; arnés completo; verificar_alcance_pr, reparto, índice y especificaciones con código 0; mutaciones m1 a m5.
- `python scripts/generar_indice_tareas.py --verificar` con código 0.
