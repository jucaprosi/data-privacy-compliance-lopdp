### ORG-23 · lectura-del-auditor-fuera-de-capa  (tanda 1)

**Contexto.** Salas: `diagnostico`, `incidentes`, `roadmap`. Depende de: nada abierto. Especificaciones: `governance/tareas/ORG-23.md` y `governance/especificaciones/ORG-23.md`.

**Cómo se ejecuta** (esta sesión no tiene el contexto del equipo; todo lo necesario está aquí y en la ficha).

- **Rama:** `tarea/juan-carlos/org-23`, creada desde `origin/main` (`git fetch origin` y `git switch -c tarea/juan-carlos/org-23 origin/main`), en un worktree propio fuera del escritorio.
- **Ficha:** en tu propio PR pon `estado = "en_curso"` en `governance/tareas/ORG-23.md`. No la marques «hecha».
- **Un PR por ficha.** No lo fusiones: el propietario se lo pasa al CTO, que lo simula y lo fusiona.
- **Entorno:** sin `.env`; la configuración sale de variables de entorno. Las pruebas que abren la base usan el PostgreSQL 16 local (`.\scripts\entorno_local.ps1`) y `exigir_base_de_pruebas()`. Nunca producción ni una base compartida.
- **No edites** `.github/workflows/`, `verificadores/`, `AGENTS.md` ni `.claude/`.
- Archivos nuevos en LF; no cambies el estilo de líneas de los existentes. Pruebas sin `import yaml` (usa `tests/_lector_yaml.py`).
- Antes de pedir revisión: `python scripts/generar_indice_tareas.py --verificar`, `python scripts/verificar_reparto.py` y el árbitro de abajo, con su salida en el PR.

**Objetivo** (en este orden):

1. `ORG-23` — Lectura del auditor en diagnóstico, incidentes y hoja de ruta: auditor en ROLES_CONSULTA

**Rastro ¤**:

- `¤rbac-tenant`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `api/routers/diagnostico_resultados.py`
  - `features/incidentes/domain/models.py`
  - `api/routers/roadmaps_hallazgos.py`
  - `tests/matriz/RM-21.py`
  - `tests/matriz/roles/auditor.py#ORG-22`
  - `tests/matriz/roles/auditor.py#ORG-23`
  - `tests/test_org23_auditor_lectura.py`

**No hagas:**

- No escribas fuera de la lista anterior.
- Cumple el contrato de `governance/especificaciones/ORG-23.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No toques producción ni una base compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ORG-23`: pytest tests/test_org23_auditor_lectura.py tests/test_matriz_permisos.py + suites existentes de diagnóstico, incidentes y hoja de ruta; mutación m1
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.
