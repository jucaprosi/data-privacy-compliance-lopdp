### BL-323 · pruebas-guardia-publica-exigir-base-de-pruebas  (tanda 69)

**Contexto.** Sala: `pruebas`. Depende de: `CI-08`, `CI-09`, `ENT-01`. Especificaciones: `governance/tareas/RET-01a.md`.

**Objetivo** (en este orden):

1. `RET-01a` — Guardia pública exigir_base_de_pruebas() en tests/conftest.py

**Rastro ¤**:

- `¤arbitro`: registrado en `VPA_MAP.md`.
- `¤seguridad`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `tests/conftest.py`
  - `tests/test_ret01a_guardia_base.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- No uses la base ni el proyecto de producción.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `RET-01a`: pytest tests/test_ret01a_guardia_base.py tests/test_plataforma_unica.py tests/test_reparto.py tests/test_indice_tareas.py tests/test_adpa_bulkhead.py; mutación: una función que no comprueba da rojo
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

