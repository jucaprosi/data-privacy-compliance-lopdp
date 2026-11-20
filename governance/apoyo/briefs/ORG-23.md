### ORG-23 · lectura-del-auditor-fuera-de-capa  (tanda 1)

**Contexto.** Salas: `diagnostico`, `incidentes`, `roadmap`. Depende de: nada abierto. Especificaciones: `governance/tareas/ORG-23.md` y `governance/especificaciones/ORG-23.md`.

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
