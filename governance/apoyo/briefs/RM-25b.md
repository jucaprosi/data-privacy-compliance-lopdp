### RM-25b · evidencia-validacion-final-exige-la-primera  (tanda 81)

**Contexto.** Sala: `roadmap`. Depende de: `RM-25a`, `DIAG-12`, `DIAG-07`, `ORG-22`, `RET-02`, `RET-03`, `ORG-22c`, `QA-09`, `RET-06`. Especificaciones: `governance/tareas/RM-25b.md` y `governance/especificaciones/RM-25b.md`.

**Modelo:** Fable (claude-fable-5-2), por decisión del propietario.

**Cómo se ejecuta** (esta sesión no tiene el contexto del equipo; todo lo necesario está aquí y en la ficha).

- **Rama:** `tarea/juan-carlos/rm-25b`, creada desde `origin/main` (`git fetch origin` y `git switch -c tarea/juan-carlos/rm-25b origin/main`), en un worktree propio fuera del escritorio.
- **Ficha:** en tu propio PR pon `estado = "en_curso"` en `governance/tareas/RM-25b.md`. No la marques «hecha».
- **Un PR por ficha.** No lo fusiones: el propietario se lo pasa al CTO, que lo simula y lo fusiona.
- **Entorno:** sin `.env`; la configuración sale de variables de entorno. Las pruebas que abren la base usan el PostgreSQL 16 local (`.\scripts\entorno_local.ps1`) y `exigir_base_de_pruebas()`. Nunca producción ni una base compartida.
- **No edites** `.github/workflows/`, `verificadores/`, `AGENTS.md` ni `.claude/`.
- Archivos nuevos en LF; no cambies el estilo de líneas de los existentes. Pruebas sin `import yaml` (usa `tests/_lector_yaml.py`).
- Antes de pedir revisión: `python scripts/generar_indice_tareas.py --verificar`, `python scripts/verificar_reparto.py` y el árbitro de abajo, con su salida en el PR.

**Objetivo** (en este orden):

1. `RM-25b` — Evidencia: la validación final exige la primera, un rol dpo o auditor y dos personas distintas (contraer)

**Rastro ¤**:

- `¤roadmap`.

**Escribe** (lista exclusiva):

  - `alembic/versions/rm25b_evidencia_exigir.py`
  - `features/roadmap/services/evidencia_engine.py`
  - `api/routers/roadmaps.py`
  - `features/roadmap/services/tareas_validadas_engine.py`
  - `tests/test_diag12_estados.py`
  - `tests/test_rm25b_validacion_final.py`
  - `features/roadmap/domain/errores.py#RM-25b`
  - `tests/matriz/RM-25b.py`
  - `tests/test_matriz_permisos.py`
  - `tests/test_rm25a_primera_validacion.py`
  - `tests/test_e2e_hoja_de_ruta_real.py`
  - `tests/test_organizacion_api.py`
  - `tests/test_roadmap_service.py`

**No hagas:**

- No escribas fuera de la lista anterior.
- Cumple el contrato de la especificación; ante una contradicción con el PRD o las invariantes, detente e informa.
- No toques producción ni una base compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `RM-25b`: pytest tests/test_rm25b_validacion_final.py tests/test_diag12_estados.py contra PostgreSQL 16 local con lopdp_app y RLS + suite completa: aprobar sin primera validación da 409 PRIMERA_VALIDACION_PENDIENTE; un coordinador que aprueba da 403 ROL_SIN_VALIDACION_FINAL; un implementador da 403; el mismo coordinador como validador final da 409; un INSERT o UPDATE directo a approved sin primera validación lo rechaza el CHECK; DIAG-12 no cuenta una tarea que aprobó un DPO sin primera validación; mutaciones documentadas: quitar el CHECK o quitar la condición de rol en la consulta hace fallar su prueba
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.
