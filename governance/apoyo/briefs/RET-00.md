### BL-309 · pruebas-arbitro-de-plataforma-unica  (tanda 69)

**Contexto.** Sala: `pruebas`. Depende de: —. Especificaciones: `governance/tareas/RET-00.md`.

**Objetivo** (en este orden):

1. `RET-00` — Árbitro de plataforma única: main solo depende de Google Cloud

**Rastro ¤**:

- `¤arbitro`: registrado en `VPA_MAP.md`.
- `¤seguridad`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `tests/plataforma_unica/dependencias.txt`
  - `tests/plataforma_unica/servicios_externos.txt`
  - `tests/plataforma_unica/variables.txt`
  - `tests/plataforma_unica/despliegue.txt`
  - `tests/plataforma_unica/catalogos.py`
  - `tests/plataforma_unica/pendientes/RET-01.txt`
  - `tests/plataforma_unica/pendientes/RET-02.txt`
  - `tests/plataforma_unica/pendientes/RET-03.txt`
  - `tests/plataforma_unica/pendientes/RET-05.txt`
  - `tests/plataforma_unica/pendientes/RET-06.txt`
  - `tests/plataforma_unica/pendientes/IA-04.txt`
  - `tests/plataforma_unica/pendientes/IA-06.txt`
  - `tests/plataforma_unica/pendientes/IA-08.txt`
  - `tests/test_plataforma_unica.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- No uses la base ni el proyecto de producción.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `RET-00`: pytest tests/test_plataforma_unica.py + tests/test_sin_neon.py + tests/test_alembic_una_cabeza.py; mutaciones documentadas por cada prueba nueva
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

