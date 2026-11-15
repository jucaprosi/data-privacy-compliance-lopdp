### BL-233 · demo-purga  (tanda 25)

**Contexto.** Proyecto EVYDENTIA (Google Cloud). Sala: `operaciones`. Depende de: `DEMO-00`, `EP-01`. Especificaciones: `governance/tareas/DEMO-05.md`, `governance/apoyo/FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md`, `governance/apoyo/UX_DEMO_EVYDENTIA.md`, PRD EVYDENTIA §5.6.

**Objetivo** (en este orden):

1. `DEMO-05` — Cloud Run Job de purga nocturna: filas y objetos de las demos vencidas

**Rastro ¤**:

- `¤demo`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `jobs/purga_demo/**`
  - `tests/test_demo_purga.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No toques `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod` ni la RLS.
- No cambies el contrato de `FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md` §1.7 ni las firmas de `demo_service.py`: si hace falta, para y consulta a Tech Lead.
- Nunca uses la base ni el proyecto de producción, ni el `.env` de la carpeta principal.
- No edites gobernanza reservada (`.github/workflows/` incluido), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas (§5.5).
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `DEMO-05`: pytest tests/test_demo_purga.py contra una base de prueba; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

