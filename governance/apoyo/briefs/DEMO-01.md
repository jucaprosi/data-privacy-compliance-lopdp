### BL-235 · demo-persona  (tanda 26)

**Contexto.** Proyecto EVYDENTIA (Google Cloud). Sala: `demo`. Depende de: `DEMO-00`, `DEMO-08`, `EP-01`. Especificaciones: `governance/tareas/DEMO-01.md`, `governance/apoyo/FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md`, `governance/apoyo/UX_DEMO_EVYDENTIA.md`, PRD EVYDENTIA §5.6.

**Objetivo** (en este orden):

1. `DEMO-01` — Persona activa y «Ver como»: resolver, 403 si es ajena y auditoría con el vendedor real

**Rastro ¤**:

- `¤demo`: registrado en `VPA_MAP.md`.
- `¤seguridad`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/demo/services/resolutor_engine.py`
  - `features/demo/services/persona_engine.py`
  - `api/routers/demo_persona.py`
  - `tests/test_demo_persona.py`

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

- `DEMO-01`: pytest tests/test_demo_persona.py + suite de seguridad y de segregación del DPO existente en verde + linter ADPA sin cruces; mutaciones documentadas
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

