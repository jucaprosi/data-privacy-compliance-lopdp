### BL-330 · frontend-estado-del-incidente-cerrar-y-reabrir  (tanda 71)

**Contexto.** Sala: `frontend`. Depende de: nada abierto. Especificaciones: `governance/tareas/INC-03f.md`.

**Objetivo** (en este orden):

1. `INC-03f` — Insignia de estado y botones Cerrar y Reabrir en la bitácora de incidentes

**Rastro ¤**:

- `¤incidentes`: registrado en `VPA_MAP.md`.
- `¤rbac-tenant`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `frontend/src/components/IncidentPlaybook.tsx`
  - `frontend/src/lib/incidentes/estado.ts`
  - `frontend/tests/incidentes/estado.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- No uses la base ni el proyecto de producción.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `INC-03f`: Playwright frontend/tests/incidentes/estado.spec.ts + tsc --noEmit + npm run build; mutaciones m1 a m4
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.
