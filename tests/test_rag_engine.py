from features.regulacion_rag.services.rag_engine import responder_consulta_normativa
from features.regulacion_rag.domain.models import ConsultaRAGInput

def test_rag_off_topic_query_rejected():
    """Verifica que el modo estricto de citas rechace consultas fuera de contexto."""
    consulta = ConsultaRAGInput(
        pregunta="¿Cuál es la receta para hacer un pastel de chocolate?",
        tenant_id="tenant-test"
    )
    resultado = responder_consulta_normativa(consulta)
    
    assert resultado.respuesta == "No puedo responder esto basándome en la normativa indexada."
    assert not resultado.citas_normativas
    assert resultado.confianza == 0.0
    assert resultado.fuente_oficial_verificada is False

def test_rag_on_topic_query_accepted():
    """Verifica que el modo estricto acepte y cite consultas sobre la LOPDP."""
    consulta = ConsultaRAGInput(
        pregunta="¿Qué dice la norma sobre la independencia del DPO?",
        tenant_id="tenant-test"
    )
    resultado = responder_consulta_normativa(consulta)
    
    assert resultado.respuesta != "No puedo responder esto basándome en la normativa indexada."
    assert len(resultado.citas_normativas) > 0
    assert resultado.confianza > 0.0
    assert resultado.fuente_oficial_verificada is True
