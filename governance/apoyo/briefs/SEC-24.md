### BL-333 · pasillo-central-sin-tenant-por-defecto  (tanda 76)

**Contexto.** Sala: `pasillo_central`. Depende de: nada abierto. Especificaciones: `governance/tareas/SEC-24.md`.

**Objetivo** (en este orden):

1. `SEC-24` — Quitar el valor por defecto de la cabecera de tenant en la dependencia común

**Rastro ¤**:

- `¤seguridad-tenant`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `api/dependencies.py`
  - `tests/test_sec24_sin_tenant_por_defecto.py`
  - `tests/snapshots/openapi_evidencias_antiguas.json`
  - `tests/test_evidencias_rutas_estables.py`
  - `tests/test_reportes_pdf.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- No uses la base ni el proyecto de producción.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `SEC-24`: pytest tests/test_sec24_sin_tenant_por_defecto.py + suite completa; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.
