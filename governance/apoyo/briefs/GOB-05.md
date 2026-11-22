### GOB-05 · adoptar-el-generador-de-indice-del-molde-de-zerag  (tanda 89)

**Contexto.** Sala: `gobernanza`. Depende de: `ADPA-10`, `CI-35`, `DEMO-03a`. Especificación: `governance/tareas/GOB-05.md`. CI-35 toca los mismos archivos: esta ficha arranca cuando CI-35 esté fusionada en `main`.

**Cómo se ejecuta** (esta sesión no tiene el contexto del equipo; todo lo necesario está aquí y en la ficha).

- **Rama:** `tarea/juan-carlos/gob-05`, creada desde `origin/main` (`git fetch origin` y `git switch -c tarea/juan-carlos/gob-05 origin/main`), en un worktree propio fuera del escritorio.
- **Ficha:** en tu propio PR pon `estado = "en_curso"` en `governance/tareas/GOB-05.md`. No la marques «hecha».
- **Un PR por ficha.** No lo fusiones: el propietario se lo pasa al CTO, que lo simula y lo fusiona.
- **Molde:** la fuente es `governance/molde/generar_indice_tareas.py` del repositorio ZERAG, en su `main`. Se lee de ahí y no se modifica desde LOPDP: lo que deba subir al molde se pide como ticket de ZERAG.
- **Entorno:** sin `.env`; la configuración sale de variables de entorno. Nunca producción ni una base compartida.
- **No edites** `.github/workflows/`, `verificadores/`, `AGENTS.md` ni `.claude/`. El punto 6 de la ficha (pasar `ZERAG_ARBITRO=1` al CI) se mide y se informa; el cambio en `.github/workflows/` lo decide el propietario.
- Archivos nuevos en LF; no cambies el estilo de líneas de los existentes.
- Antes de pedir revisión: `python scripts/generar_indice_tareas.py --verificar`, `python scripts/verificar_reparto.py` y el árbitro de abajo, con su salida en el PR.

**Objetivo** (en este orden):

1. `GOB-05` — Adoptar el generador de índice del molde de ZERAG (claves de configuración, cabecera de imports, sugerencia de ruta y exenciones con caducidad) y retirar el mecanismo propio de exenciones

**Rastro ¤**:

- `¤arbitro`.

**Escribe** (lista exclusiva):

  - `scripts/generar_indice_tareas.py`
  - `governance/tareas/_exenciones_propiedad.txt`
  - `tests/test_generar_indice_tareas_arbol.py`
  - `governance/tareas/GOB-05.md`

**No hagas:**

- No escribas fuera de la lista anterior. No toques `TASKS.md`.
- No sobrescribas el generador a ciegas: primero el `diff` con el molde y una decisión por cada diferencia, escrita en el PR.
- Cumple la ficha; ante una contradicción con el PRD o las invariantes, detente e informa.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `GOB-05`: pytest tests/test_generar_indice_tareas_arbol.py tests/test_indice_tareas.py + python scripts/generar_indice_tareas.py --verificar
- `python scripts/generar_indice_tareas.py --verificar` con código 0.
