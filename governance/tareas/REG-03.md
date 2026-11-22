+++
id = "REG-03"
titulo = "Compuertas de vectores, caché y corpus citable de la sala regulacion_rag"
ola = "backlog"
estado = "hecha"
sala = "regulacion_rag"
depende_de = ["IA-12", "NORM-03", "VTX-01"]
propiedad = ["features/regulacion_rag/regulacion_rag_service.py#REG-03", "features/regulacion_rag/services/vertex_context_cache.py", "tests/test_reg03_compuertas_corpus.py"]
crea = ["tests/test_reg03_compuertas_corpus.py"]
arbitro = "pytest tests/test_reg03_compuertas_corpus.py tests/test_norm03_impacto_hitl.py; mutaciones m1 a m3."
rastros = ["¤vertex-cache", "¤arbitro"]
+++

# REG-03 · Compuertas de vectores, caché y corpus citable de la sala regulacion_rag

**Contrato:** `governance/especificaciones/REG-03.md` (manda sobre esta ficha).

**Origen.** Pedido del CTO (2026-11-21). NORM-03 dejó dos compuertas abiertas, `vectorizar_fragmentos` y `regenerar_cache_normativo`: el pasillo lanza `NotImplementedError`. Medido además: tampoco existen `obtener_o_crear_cache_normativo` ni `corpus_citable`, que ya llaman VTX-01 y BOV-04.

## Entrega
- Las cuatro funciones en la compuerta `regulacion_rag_service`, sobre `vertex_context_cache` y el pasillo de inferencia (IA-12).

## Límites
- El pasillo `app_core/pasillo/regulacion_rag.py` no cambia: ya llama a esos nombres.
