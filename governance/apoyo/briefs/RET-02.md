### BL-313 · roadmap-almacen-gcs-y-generacion-sin-cola  (tanda 71)

**Contexto.** Sala: `roadmap, evidencias`. Depende de: `RET-01`, `EVI-04`, `RM-26`. Especificaciones: `governance/tareas/RET-02.md`, `governance/tareas/RET-03.md`.

**Objetivo** (en este orden):

1. `RET-02` — Almacén de evidencias del roadmap en Google Cloud Storage
2. `RET-03` — Generación de la hoja de ruta sin cola externa

**Rastro ¤**:

- `¤evidencias`: registrado en `VPA_MAP.md`.
- `¤roadmap`: registrado en `VPA_MAP.md`.
- `¤seguridad-tenant`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `api/routers/roadmaps.py`
  - `features/roadmap/services/evidencia_engine.py`
  - `app_core/storage/r2.py`
  - `app_core/storage/gcs.py`
  - `app_core/storage/limites.py`
  - `features/evidencias/services/evidencias_engine.py`
  - `features/evidencias/services/custodia_generados_engine.py`
  - `features/evidencias/services/paquete_inspeccion_engine.py`
  - `frontend/next.config.ts`
  - `frontend/src/lib/roadmap/cliente.ts`
  - `frontend/src/lib/roadmap/mockServer.ts`
  - `requirements.txt`
  - `tests/test_ret02_almacen_gcs.py`
  - `tests/test_evidencias_subida_firmada.py`
  - `tests/test_evidencia_validacion_servidor.py`
  - `frontend/tests/roadmap/evidencia.spec.ts`
  - `tests/plataforma_unica/pendientes/RET-02.txt`
  - `app_core/queue/redis_client.py`
  - `features/roadmap/roadmap_service.py`
  - `features/roadmap/services/generacion_engine.py`
  - `features/roadmap/services/generacion_en_linea.py`
  - `tests/test_redis_client.py`
  - `tests/test_roadmap_service.py`
  - `tests/test_ret03_sin_cola.py`
  - `frontend/tests/roadmap/generacion.spec.ts`
  - `tests/plataforma_unica/pendientes/RET-03.txt`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- No uses la base ni el proyecto de producción.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `RET-02`: pytest tests/test_ret02_almacen_gcs.py tests/test_evidencias_subida_firmada.py tests/test_evidencia_validacion_servidor.py contra un PostgreSQL 16 local + Playwright de frontend/tests/roadmap/evidencia.spec.ts + tsc --noEmit + suite completa; prueba de mutación documentada
- `RET-03`: pytest tests/test_ret03_sin_cola.py tests/test_roadmap_service.py contra un PostgreSQL 16 local + Playwright de frontend/tests/roadmap/generacion.spec.ts + tsc --noEmit + suite completa; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

