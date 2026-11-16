# ¤adpa
"""Capacidades de la sala regulacion_rag para otras salas (pasillo central, ADPA §3).

Cada función importa la compuerta en su cuerpo; aquí no hay lógica de negocio.
Cada tarea escribe solo dentro de su sección reservada.
"""

# === ADPA-06 ===
# Andamiaje del pasillo de esta sala: secciones reservadas abajo.
# === fin ADPA-06 ===

# === DIAG-04 ===
# === fin DIAG-04 ===

# === DIAG-07 ===
# === fin DIAG-07 ===

# === NORM-03 ===
# ¤vertex-cache Vectorización de fragmentos y pedido de regeneración de la caché del corpus (VTX-01, R4).
async def vectorizar_fragmentos(textos, modelo):
    """Vectores de `text-embedding-005`; sin la compuerta de la sala lanza NotImplementedError (el llamador sigue)."""
    from features.regulacion_rag import regulacion_rag_service

    vectorizar = getattr(regulacion_rag_service, "vectorizar_fragmentos", None)
    if vectorizar is None:
        raise NotImplementedError("vectorizar_fragmentos")
    return await vectorizar(textos, modelo)


def pedir_regeneracion_cache(corpus_sha256: str) -> None:
    """Pide regenerar la caché de contexto con el nuevo `corpus_sha256`; sin la compuerta lanza NotImplementedError."""
    from features.regulacion_rag import regulacion_rag_service

    regenerar = getattr(regulacion_rag_service, "regenerar_cache_normativo", None)
    if regenerar is None:
        raise NotImplementedError("regenerar_cache_normativo")
    regenerar(corpus_sha256)
# === fin NORM-03 ===

# === REG-01 ===
# ¤paquete-normativo
async def parametros_normativos_publicados(session, codigo: str) -> list:
    """Parámetros del paquete publicado (R4): las salas leen plazo y unidad de aquí, no de una constante."""
    from features.regulacion_rag import regulacion_rag_service

    return await regulacion_rag_service.parametros_publicados(session, codigo)
# === fin REG-01 ===

# === VTX-01 ===
def obtener_o_crear_cache_normativo(modelo):
    """Descriptor de la caché de Vertex del corpus normativo vigente (compuerta de la sala)."""
    from features.regulacion_rag import regulacion_rag_service

    return regulacion_rag_service.obtener_o_crear_cache_normativo(modelo)


def corpus_citable():
    """{id: fundamento} del corpus normativo, para validar las citas del copiloto."""
    from features.regulacion_rag import regulacion_rag_service

    return regulacion_rag_service.corpus_citable()
# === fin VTX-01 ===
