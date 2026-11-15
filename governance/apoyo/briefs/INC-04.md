### BL-320 · incidentes-marca-de-notificacion-pendiente-veraz  (tanda 66)

**Contexto.** Sala: `incidentes`. Depende de: `INC-02`, `INC-03`. Especificaciones: `governance/tareas/INC-04.md`, `governance/especificaciones/INC-04.md`.

**Objetivo** (en este orden):

1. `INC-04` — La marca de notificación pendiente del cierre ya no se escribe falsa

**Rastro ¤**:

- `¤incidentes`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/incidentes/services/estado_engine.py`
  - `features/incidentes/domain/estado.py`
  - `tests/test_inc03_estado_incidente.py`
  - `tests/test_inc04_marca_notificacion.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- Nunca uses la base ni el proyecto de producción, ni el `.env` de la carpeta principal.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `INC-04`: pytest tests/test_inc04_marca_notificacion.py tests/test_inc03_estado_incidente.py contra un PostgreSQL 16 local (incluido RLS con lopdp_app) + tests/test_incidentes_asistente.py; mutaciones documentadas por escenario
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.


