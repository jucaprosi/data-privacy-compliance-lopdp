### DEMO-05c · purga-demo-politicas-por-rol  (tanda 1)

**Contexto.** Sala: `demo`. Depende de: nada abierto. Especificaciones: `governance/tareas/DEMO-05c.md` y `governance/especificaciones/DEMO-05c.md`.

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
