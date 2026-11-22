### REG-03 · compuertas-de-vectores-cach-y-corpus-citable-de-la-sala-regu  (tanda 87)

**Contexto.** Sala: `regulacion_rag`. Depende de: `IA-12`, `NORM-03`, `VTX-01`. Especificaciones: `governance/tareas/REG-03.md` y `governance/especificaciones/REG-03.md` (manda la especificación).

**Cómo se ejecuta** (esta sesión no tiene el contexto del equipo; todo lo necesario está aquí y en la ficha).

- **Rama:** `tarea/juan-carlos/reg-03`, creada desde `origin/main` (`git fetch origin` y `git switch -c tarea/juan-carlos/reg-03 origin/main`), en un worktree propio fuera del escritorio.
- **Ficha:** en tu propio PR pon `estado = "en_curso"` en `governance/tareas/REG-03.md`. No la marques «hecha».
- **Un PR por ficha.** No lo fusiones: el propietario se lo pasa al CTO, que lo simula y lo fusiona.
- **Entorno:** sin `.env`; la configuración sale de variables de entorno. Las pruebas que abren la base usan el PostgreSQL 16 local (`.\scripts\entorno_local.ps1`) y `exigir_base_de_pruebas()`. Nunca producción ni una base compartida.
- **No edites** `.github/workflows/`, `verificadores/`, `AGENTS.md` ni `.claude/`.
- Archivos nuevos en LF; no cambies el estilo de líneas de los existentes. Pruebas sin `import yaml` (usa `tests/_lector_yaml.py`).
- Antes de pedir revisión: `python scripts/generar_indice_tareas.py --verificar`, `python scripts/verificar_reparto.py` y el árbitro de abajo, con su salida en el PR.

**Objetivo** (en este orden):

1. `REG-03` — Compuertas de vectores, caché y corpus citable de la sala regulacion_rag

**Orden.** Depende de `IA-12`, que se lanza antes (tanda 86). Si IA-12 aún no está en `main`, no empieces.

**Rastro ¤**:

- `¤vertex-cache`, `¤arbitro`.

**Escribe** (lista exclusiva):

  - `features/regulacion_rag/regulacion_rag_service.py#REG-03`
  - `features/regulacion_rag/services/vertex_context_cache.py`
  - `tests/test_reg03_compuertas_corpus.py`

**No hagas:**

- No escribas fuera de la lista anterior. Si tu ficha tiene secciones `#ID`, escribe solo dentro de tus marcas.
- Cumple el contrato de la especificación; ante una contradicción con el PRD o las invariantes, detente e informa.
- No toques producción ni una base compartida; no despliegues.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `REG-03`: pytest tests/test_reg03_compuertas_corpus.py tests/test_norm03_impacto_hitl.py; mutaciones m1 a m3.
- `python scripts/generar_indice_tareas.py --verificar` con código 0.
