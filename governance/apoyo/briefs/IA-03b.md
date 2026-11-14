### BL-305 · evidencia-de-humo-de-la-compuerta-con-vertex-real  (tanda 65)

**Contexto.** Sala: `inferencia`. Depende de: `IA-03`. Especificaciones: `governance/tareas/IA-03b.md`.

**Objetivo** (en este orden):

1. `IA-03b` — Evidencia de humo de la compuerta de inferencia con Vertex AI real (la corre el propietario)

**Rastro ¤**:

- `¤gemini-vertex`: registrado en `VPA_MAP.md`.
- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `governance/operaciones/EVIDENCIA_HUMO_VERTEX.md`
  - `governance/operaciones/BRIEF_PROPIETARIO_VERTEX.md`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- Nunca uses la base ni el proyecto de producción, ni el `.env` de la carpeta principal.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `IA-03b`: evidencia humana, no es un árbitro de CI: el propietario corre VERTEX_HUMO=1 python -m pytest tests/test_ia03_humo_vertex.py con las credenciales de la cuenta de servicio y entrega la salida al CTO; el Tech Lead la registra en governance/operaciones/EVIDENCIA_HUMO_VERTEX.md
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.


