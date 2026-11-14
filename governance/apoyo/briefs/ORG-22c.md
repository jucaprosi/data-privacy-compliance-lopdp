### BL-316 · matriz-de-permisos-rutas-de-dlp-y-boveda  (tanda 66)

**Contexto.** Sala: `organizacion`. Depende de: `ORG-22`, `DLP-01`, `BOV-01`. Especificaciones: `governance/tareas/ORG-22c.md`.

**Objetivo** (en este orden):

1. `ORG-22c` — Rutas de descubrimiento DLP y bóveda en la matriz de permisos, con sus filas y mutación

**Rastro ¤**:

- `¤rbac-tenant`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `tests/test_matriz_permisos.py`
  - `tests/matriz/DLP-01.py`
  - `tests/matriz/BOV-01.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- Nunca uses la base ni el proyecto de producción, ni el `.env` de la carpeta principal.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `ORG-22c`: pytest tests/test_matriz_permisos.py: con los prefijos /api/v1/dlp-discovery y /api/v1/boveda-cloud en PREFIJOS_MATRIZ no queda ruta registrada sin fila; mutación documentada: quitar una fila de la matriz hace fallar la detección de rutas sin cubrir; revisión de Seguridad
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.


