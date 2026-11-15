### BL-309 · pruebas-eliminar-las-que-vigilaban-plataformas-retiradas  (tanda 69)

**Contexto.** Sala: `pruebas`. Depende de: nada abierto. Especificaciones: `governance/tareas/RET-00.md`.

**Objetivo** (en este orden):

1. `RET-00` — Eliminar las pruebas que vigilaban plataformas retiradas

**Rastro ¤**:

- `¤arbitro`: registrado en `VPA_MAP.md`.
- `¤seguridad`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `tests/plataforma_unica/catalogos.py`
  - `tests/plataforma_unica/dependencias.txt`
  - `tests/plataforma_unica/despliegue.txt`
  - `tests/plataforma_unica/servicios_externos.txt`
  - `tests/plataforma_unica/variables.txt`
  - `tests/plataforma_unica/pendientes/RET-01.txt`
  - `tests/plataforma_unica/pendientes/RET-02.txt`
  - `tests/plataforma_unica/pendientes/RET-03.txt`
  - `tests/plataforma_unica/pendientes/RET-05.txt`
  - `tests/plataforma_unica/pendientes/RET-06.txt`
  - `tests/plataforma_unica/pendientes/IA-04.txt`
  - `tests/plataforma_unica/pendientes/IA-06.txt`
  - `tests/plataforma_unica/pendientes/IA-08.txt`
  - `tests/test_plataforma_unica.py`
  - `tests/sin_neon/permitidos.txt`
  - `tests/sin_neon/pendientes/FIRMA-02.txt`
  - `tests/sin_neon/pendientes/NEON-01.txt`
  - `tests/sin_neon/pendientes/NEON-02.txt`
  - `tests/sin_neon/pendientes/NEON-03.txt`
  - `tests/sin_neon/pendientes/NEON-04.txt`
  - `tests/test_sin_neon.py`
  - `tests/test_ci17_ci_sin_neon.py`
  - `tests/test_vercel_despliegue.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- No uses la base ni el proyecto de producción.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `RET-00`: suite completa en verde en el CI + pytest tests/test_indice_tareas.py tests/test_reparto.py; ninguno de los archivos de la propiedad existe tras el merge (revisión del PR)
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.
