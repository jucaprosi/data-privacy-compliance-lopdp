### BL-109 · quien-responde-y-quien-sella  (tanda 34)

**Contexto.** Sala: `diagnostico, frontend`. Depende de: `DIAG-04`, `DIAG-05`, `ADPA-05`, `ADPA-06`, `ADPA-07`, `ADPA-11`, `DIAG-07a`, `DIAG-07b`, `DIAG-14`, `EVI-01b`, `EVI-02`. Especificaciones: `governance/tareas/DIAG-07.md`.

**Objetivo** (en este orden):

1. `DIAG-07` — Responden el administrador y los encargados del diagnóstico; el DPO revisa con la grilla declarado/verificado, objeta y sella

**Rastro ¤**:

- `¤diagnostico`: registrado en `VPA_MAP.md`.
- `¤dpo-independencia`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261101_diagnostico_objeciones.py`
  - `features/diagnostico/services/objeciones_engine.py`
  - `features/diagnostico/diagnostico_service.py#DIAG-07`
  - `api/routers/diagnostico_respuestas.py`
  - `api/routers/diagnostico_resultados.py`
  - `tests/test_diagnostico_quien_responde.py`
  - `tests/matriz/DIAG-07.py`
  - `frontend/src/components/diagnostico/GrillaRevision.tsx`
  - `frontend/src/lib/diagnostico/objeciones.ts`
  - `frontend/tests/diagnostico/revision.spec.ts`
  - `features/diagnostico/domain/errores.py#DIAG-07`
  - `app_core/pasillo/diagnostico.py#DIAG-07`
  - `tests/test_diagnostico_respuestas.py`
  - `tests/test_diagnostico_resultados.py`
  - `frontend/tests/diagnostico/solo-dpo.spec.ts`
  - `frontend/src/lib/diagnostico/roles.ts`
  - `app_core/pasillo/roadmap.py#DIAG-07`
  - `app_core/pasillo/organizacion.py#DIAG-07`
  - `app_core/pasillo/regulacion_rag.py#DIAG-07`
  - `frontend/src/components/DiagnosticCanvas.tsx#DIAG-07`
  - `frontend/src/components/layout/menus/index.ts#DIAG-07`
  - `frontend/src/components/layout/pantallas/index.tsx#DIAG-07`
  - `frontend/src/lib/diagnostico/clienteRespuestas.ts`
  - `frontend/tests/diagnostico/simulador.ts`
  - `frontend/tests/diagnostico/escala.spec.ts`
  - `frontend/tests/diagnostico/escala-activa.spec.ts`
  - `frontend/tests/diagnostico/no-aplica.spec.ts`
  - `frontend/tests/diagnostico/persistencia.spec.ts`
  - `frontend/tests/diagnostico/prueba-y-real.spec.ts`
  - `frontend/tests/diagnostico/sellado.spec.ts`
  - `frontend/tests/diagnostico/guardar-como-admin.spec.ts`
  - `frontend/src/components/diagnostico/NotaSoloDpo.tsx`
  - `api/routers/preanalisis.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- Nunca uses la base ni el proyecto de producción, ni el `.env` de la carpeta principal.
- No edites gobernanza reservada (`.github/workflows/` incluido), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `DIAG-07`: pytest tests/test_diagnostico_quien_responde.py contra un PostgreSQL 16 local en contenedor (incluido RLS con lopdp_app) + suite completa + vigilantes + Playwright de frontend/tests/diagnostico + tsc --noEmit + npm run build; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

