# VTX-01 · Vertex AI Context Caching para el Corpus Normativo LOPDP/SPDP
`¤sdd` `¤vertex-cache` `¤copiloto-ia` `¤regulation-code`

## 1. Datos

Estructura `VertexCorpusCacheDescriptor` (`cache_name: str`, `corpus_version: str`, `corpus_sha256: str`, `ttl_seconds: int`, `token_count: int`).

## 2. API

- Compuerta `obtener_o_crear_cache_normativo()` en `regulacion_rag_service.py#VTX-01`
- Compuerta `consultar_copiloto_con_cache()` en `copilot_service.py#VTX-01`

## 3. Reglas

- **R1 · Reutilización por hash de corpus.** Si existe un `CachedContent` vigente cuyo `corpus_sha256` coincide con la versión activa del paquete normativo, se reutiliza sin reenviar el corpus completo.
- **R2 · Filtro DLP Módulo 10 obligatorio (`INV_LOPDP_DLP_ECUADORIAN_CEDULA_MODULO10`).** Todo prompt pasa por el redactor determinista de cédulas antes de salir hacia Vertex AI.
- **R3 · Citación cerrada obligatoria (`INV_LOPDP_AI_RAG_STRICT_CITATION`).** Si la respuesta no referencia un artículo del corpus en caché, devuelve declaración de incertidumbre.

## 4. Interfaz

Transparente para los consumidores de `regulacion_rag` y `ai_copilot`.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** dos consultas normativas consecutivas sobre la misma versión del corpus LOPDP, **cuando** se invoca `consultar_copiloto_con_cache`, **entonces** la segunda reutiliza el mismo `cache_name` de Vertex AI y cita el artículo oficial. | `test_vertex_context_cache_reutiliza_corpus_y_cita_fuente` |
| **Dado** una consulta al copiloto que incluye un número de cédula ecuatoriana válido, **cuando** se procesa antes de llamar a Vertex AI, **entonces** la cédula queda enmascarada como `[CEDULA-REDACTADA]`. | `test_vertex_rag_redacta_cedula_modulo10_prevuelo` |

## 6. Trazabilidad

- PRD §6, §8.4 e invariantes `INV_LOPDP_AI_RAG_STRICT_CITATION` e `INV_LOPDP_DLP_ECUADORIAN_CEDULA_MODULO10`.
