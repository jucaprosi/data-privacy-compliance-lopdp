### BL-336 · pasillo-central-cache-control-no-store-por-defecto  (tanda 76)

**Contexto.** Sala: `pasillo_central`. Depende de: nada abierto. Especificaciones: `governance/tareas/SEC-25.md`.

**Objetivo** (en este orden):

1. `SEC-25` — Cabecera Cache-Control: no-store por defecto en /api/v1

**Rastro ¤**:

- `¤seguridad-tenant`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `app_core/seguridad/no_store.py`
  - `main.py#SEC-25`
  - `tests/test_sec25_no_store.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- No uses la base ni el proyecto de producción.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `SEC-25`: pytest tests/test_sec25_no_store.py + suite completa; mutación: quitar el middleware → rojo
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

