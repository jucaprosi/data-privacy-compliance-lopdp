+++
id = "ORG-12"
titulo = "El coordinador fija el área de una tarea al distribuirla (las tareas generadas no la traen)"
ola = "D"
estado = "hecha"
sala = "roadmap"
depende_de = ["RM-08", "ORG-00", "ORG-08", "QA-06", "FE-01", "FE-03", "FE-07", "QA-01"]
propiedad = ["api/routers/roadmaps_asignacion.py", "features/roadmap/services/tarea_asignacion_engine.py", "tests/test_roadmap_tarea_asignacion.py", "tests/test_e2e_hoja_de_ruta_real.py", "frontend/src/components/modules/roadmap/olas/OlasView.tsx", "frontend/src/lib/roadmap/cliente.ts", "frontend/src/store/useRoadmapStore.ts", "frontend/src/lib/roadmap/mockServer.ts", "frontend/tests/roadmap/olas.spec.ts", "frontend/tests/roadmap/e2e/**"]
arbitro = "pytest tests/test_roadmap_tarea_asignacion.py tests/test_e2e_hoja_de_ruta_real.py contra una rama Neon de revisión + suite completa + Playwright de frontend/tests/roadmap + tsc --noEmit y next build; prueba de mutación documentada"
rastros = ["¤roadmap", "¤rbac-tenant"]
+++

# ORG-12 · El coordinador fija el área al distribuir

**Objetivo.** QA-06 demostró que en el backend real **el recorrido principal de la hoja de ruta no se completa**: la generación crea las tareas sin `area_id` (`generacion_en_linea.py` no lo rellena), ningún endpoint permite dárselo, y la asignación al responsable lo exige (422 `RESPONSABLE_AREA_MISMATCH`). La prueba de Playwright del criterio 12 pasa porque el simulador del frontend inventa `area_id: "area-001"`.

## Decisión del propietario (2026-10-23): opción A
**El área la fija el coordinador al distribuir la tarea**, en el mismo acto de asignarla: es quien conoce las áreas al distribuir, no depende de la IA y encaja con su papel en el PRD §5.2 («Distribuir tareas a responsables»).

## Entrega
- **`POST /api/v1/roadmaps/tasks/{task_id}/assign`** acepta `area_id` opcional junto a `responsable_id` (solo `coordinador`, como hoy):
  - Si la tarea **no tiene área**, `area_id` es **obligatorio**; sin él, 422 con un mensaje que lo pide (no `RESPONSABLE_AREA_MISMATCH`).
  - Si se envía, el área debe existir en la organización (404 si no) y estar dentro del alcance del responsable (`allowed_area_ids`); si no, 422 `RESPONSABLE_AREA_MISMATCH` como hoy.
  - Si la tarea **ya tiene área** y se envía otra, se cambia (redistribución); si no se envía, se conserva y se valida como hoy.
  - Área y responsable se fijan en la **misma transacción**; el evento `task_assigned` de `task_audit_log` incluye el área anterior y la nueva.
- **Pantalla «Olas & Tareas»** (`OlasView`): al asignar, el coordinador elige el área (preseleccionada si la tarea ya tiene una) y el responsable; la lista de responsables se filtra por el área elegida. Cliente y store envían `area_id`.
- **Simulador del frontend** (`mockServer.ts`): las tareas generadas **dejan de traer área inventada**, y la asignación simulada aplica las mismas reglas que el backend. Se ajustan las pruebas de Playwright afectadas (`olas.spec.ts` y el recorrido del criterio 12 en `frontend/tests/roadmap/e2e/`).
- **QA-06** (`tests/test_e2e_hoja_de_ruta_real.py`): se **retira** el `xfail` de `test_tarea_generada_se_puede_asignar` (pasa al asignar con área) y el paso declarado que daba el área por la base; el recorrido completo asigna con `area_id` por la API.
- Pruebas de backend (`test_roadmap_tarea_asignacion.py`): asignar una tarea sin área con `area_id` válido (200 y área persistida); sin `area_id` (422 con el mensaje nuevo); área de otra organización o inexistente (404); área fuera del alcance del responsable (422); redistribuir a otra área; rol distinto de coordinador (403); evento de auditoría con área anterior y nueva.
- **Prueba de mutación documentada:** ignorar el `area_id` recibido y comprobar que `test_tarea_generada_se_puede_asignar` vuelve a fallar.

## Límites
- No cambia la generación con IA (la opción B, que la IA proponga el área, queda descartada por ahora).
- No cambia quién puede asignar ni el alcance por área del responsable.
- Sin migración: `roadmap_tasks.area_id` ya existe.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks `Arnés Físico Determinista` y `Playwright Frontend` del PR están en verde. No modificó ningún archivo fuera de su propiedad.
