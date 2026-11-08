+++
id = "VTX-01"
titulo = "Vertex AI Context Caching sobre el corpus normativo LOPDP/SPDP e inferencia con filtro DLP pre-vuelo"
ola = "D"
estado = "pendiente"
sala = "regulacion_rag, ai_copilot"
depende_de = ["ADPA-03", "ADPA-05", "ADPA-06", "GCP-01", "REG-02", "RM-02", "SEC-03"]
propiedad = ["features/regulacion_rag/services/vertex_context_cache.py", "features/regulacion_rag/regulacion_rag_service.py#VTX-01", "features/regulacion_rag/domain/errores.py#VTX-01", "features/ai_copilot/services/vertex_cached_rag_engine.py", "features/ai_copilot/ai_copilot_service.py#VTX-01", "features/ai_copilot/domain/errores.py#VTX-01", "app_core/pasillo/regulacion_rag.py#VTX-01", "app_core/pasillo/ai_copilot.py#VTX-01", "tests/test_vtx01_vertex_context_caching.py"]
arbitro = "pytest tests/test_vtx01_vertex_context_caching.py + suite completa + vigilantes"
rastros = ["¤gemini-vertex", "¤vertex-cache", "¤copiloto-ia", "¤regulation-code"]
+++
# VTX-01 · Vertex AI Context Caching sobre el corpus normativo LOPDP/SPDP e inferencia con filtro DLP pre-vuelo

## Entrega
- Gestor `features/regulacion_rag/services/vertex_context_cache.py` que empaqueta el corpus normativo estático de Ecuador (LOPDP, RGLOPDP y resoluciones SPDP vigentes) en un `CachedContent` versionado de Vertex AI por `corpus_sha256` para los modelos **Google Gemini (`gemini-2.5-pro`, `gemini-2.5-flash` y `text-embedding-005`)**, reutilizando el identificador de caché entre consultas para ahorrar hasta el 90% de tokens de entrada.
- Motor `features/ai_copilot/services/vertex_cached_rag_engine.py` que ejecuta inferencia sobre **Google Gemini en Vertex AI** (`gemini-2.5-pro` para dictámenes complejos y `gemini-2.5-flash` para consultas de baja latencia), redacta preventivamente cualquier cédula ecuatoriana (Módulo 10) antes de invocar Vertex AI y exige cita expresa de artículo y norma (`INV_LOPDP_AI_RAG_STRICT_CITATION`).

## Pruebas
- `pytest tests/test_vtx01_vertex_context_caching.py` comprueba la reutilización del `cache_id` mientras el `corpus_sha256` no cambie, la invalidación automática ante una reforma normativa, la redacción DLP pre-inferencia y la citación obligatoria.
