### BL-328 · migraciones-comentarios-sin-plataformas-retiradas  (tanda 70)

**Contexto.** Sala: `pasillo_central`. Depende de: `RET-00`, `RET-01a`. Especificaciones: `governance/tareas/RET-10.md`.

**Objetivo** (en este orden):

1. `RET-10` — Comentarios de las migraciones aplicadas sin nombrar plataformas retiradas

**Rastro ¤**:

- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261008_app_role_rls.py`
  - `alembic/versions/20261108_biblioteca_capacidades_propietario.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- No uses la base ni el proyecto de producción.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `RET-10`: pytest tests/test_alembic_una_cabeza.py + suite completa en el CI; el AST de cada archivo, sin docstrings, queda idéntico al de origin/main (se comprueba una sola vez al revisar el PR)
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.
