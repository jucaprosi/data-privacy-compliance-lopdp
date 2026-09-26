"""Compuerta pública de la sala ADPA: Regulación y Copiloto RAG."""
from features.regulacion_rag.domain.models import ConsultaRAGInput, RespuestaRAGOutput
from features.regulacion_rag.services.rag_engine import responder_consulta_normativa
from features.regulacion_rag.domain.corpus import CORPUS_VERSION
from features.regulacion_rag.services.implementation_guides import obtener_guia_brecha
from features.regulacion_rag.services.rag_engine import buscar_fundamentos

def consultar_corpus_spdp(consulta: ConsultaRAGInput) -> RespuestaRAGOutput:
    """Ejecuta una consulta sobre el corpus oficial garantizando citas y ausencia de alucinaciones."""
    return responder_consulta_normativa(consulta)
