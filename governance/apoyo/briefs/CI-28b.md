### CI-28b · revision-alembic-en-todas-las-cabezas  (tanda 25)

**Contexto.** Sala(s): `gobernanza`. Depende de: `CI-18` (hecha). Especificaciones: `governance/tareas/CI-28b.md` y `governance/especificaciones/CI-28b.md`.

**Objetivo** (en este orden):

1. `CI-28b` — Comprobación de la revisión de Alembic en todas las cabezas

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤revision-alembic`: comprobación 5 del verificador.

**Escribe** (lista exclusiva):

  - `scripts/verificar_cloudsql_conexion.py`
  - `tests/test_gcp04_cloudsql_migration_cutover.py`

**No hagas:**

- No escribas fuera de la lista anterior.
- Cumple el contrato de `governance/especificaciones/CI-28b.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No toques producción ni una base compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `CI-28b`: pytest tests/test_gcp04_cloudsql_migration_cutover.py tests/test_alembic_cabeza_por_sala.py (con TEST_DATABASE_URL de PostgreSQL 16) + python scripts/generar_indice_tareas.py --verificar; mutación m1
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.
