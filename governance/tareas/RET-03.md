+++
id = "RET-03"
titulo = "Generación de la hoja de ruta sin cola externa"
ola = "backlog"
estado = "pendiente"
sala = "roadmap"
depende_de = ["RET-02", "BIB-208", "BIB-302", "BIB-303", "DEMO-03c", "DIAG-12", "ORG-15", "RM-18", "RM-22", "RM-25a", "RM-25c", "RM-26"]
propiedad = ["app_core/queue/redis_client.py", "features/roadmap/roadmap_service.py", "features/roadmap/services/generacion_engine.py", "features/roadmap/services/generacion_en_linea.py", "api/routers/roadmaps.py", "frontend/src/lib/roadmap/cliente.ts", "frontend/src/lib/roadmap/mockServer.ts", "tests/test_redis_client.py", "tests/test_roadmap_service.py", "tests/test_ret03_sin_cola.py", "frontend/tests/roadmap/generacion.spec.ts", "tests/plataforma_unica/pendientes/RET-03.txt"]
crea = ["tests/test_ret03_sin_cola.py"]
arbitro = "pytest tests/test_ret03_sin_cola.py tests/test_roadmap_service.py contra un PostgreSQL 16 local + Playwright de frontend/tests/roadmap/generacion.spec.ts + tsc --noEmit + suite completa; prueba de mutación documentada"
rastros = ["¤roadmap"]
+++

# RET-03 · Generación sin cola externa

Diseño del Arquitecto ADPA (2026-11-13): `governance/especificaciones/RET-03.md`. Modelo sugerido: sonnet. Va después de RET-02 (comparten el router y el cliente) y antes de IA-06, que posee `generacion_engine.py`.

**Problema.** La generación vigente es la en línea (RM-18). La cola con `get_job` y `enqueue_generation` ya no se usa.

**Entrega.**
- Se retira `app_core/queue/redis_client.py`, `enqueue_generation`, `get_job`, `pop_job`, `get_job_status`, sus exportaciones en `roadmap_service.py` y la ruta `GET /roadmaps/jobs/{job_id}`. `POST /roadmaps/generate` conserva su contrato.
- Antes de retirar el cliente (`getJob` en `cliente.ts`, su rama en `mockServer.ts` y el tipo `RoadmapJobStatus`), la ficha comprueba si alguna pantalla lo llama; si alguna lo usa, se detiene e informa.
- Sin tabla de trabajos nueva. El paquete `redis` se queda solo por la caché de GCP-06.

**Orden.** RM-25b y RET-02 comparten `api/routers/roadmaps.py` y `cliente.ts`: RET-02 → RET-03 → RM-25b. IA-06 va después.

