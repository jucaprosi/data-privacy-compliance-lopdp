"""Enrutador REST para la Sala ADPA: Regulación y Copiloto RAG."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.dependencies import obtener_tenant_id_actual
from features.regulacion_rag.regulacion_rag_service import consultar_corpus_spdp
from features.regulacion_rag.domain.models import ConsultaRAGInput

router = APIRouter(prefix="/rag", tags=["Regulación como Código y Copiloto RAG"])

class ConsultaRAGRequest(BaseModel):
    pregunta: str = Field(..., description="Pregunta jurídica o técnica sobre la normativa de privacidad")

@router.post("/consulta")
def consultar_rag(
    payload: ConsultaRAGRequest,
    tenant_id: str = Depends(obtener_tenant_id_actual),
):
    """Consulta el corpus oficial de la LOPDP garantizando cero alucinación y citas legales verificadas."""
    consulta = ConsultaRAGInput(
        pregunta=payload.pregunta,
        tenant_id=tenant_id,
    )
    resultado = consultar_corpus_spdp(consulta)
    return {
        "pregunta": payload.pregunta,
        "respuesta": resultado.respuesta,
        "citas_normativas": resultado.citas_normativas,
        "confianza": resultado.confianza,
        "fuente_oficial_verificada": resultado.fuente_oficial_verificada,
    }
