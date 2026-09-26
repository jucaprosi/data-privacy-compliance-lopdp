from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.dependencies import obtener_tenant_id_actual
from features.regulacion_rag.regulacion_rag_service import consultar_corpus_spdp
from features.regulacion_rag.domain.models import ConsultaRAGInput

router = APIRouter(prefix="/rag", tags=["RAG Copilot API"])

class QueryPayload(BaseModel):
    query: str = Field(..., description="Pregunta a consultar en el corpus LOPDP")

from app_core.dlp_sanitizer import sanitizar_texto_pii

@router.post("/query")
def rag_query(
    payload: QueryPayload,
    tenant_id: str = Depends(obtener_tenant_id_actual),
):
    """Endpoint de consulta estricta RAG."""
    # Sanitización DLP pre-inferencia estricta
    pregunta_segura = sanitizar_texto_pii(payload.query)
    
    consulta = ConsultaRAGInput(
        pregunta=pregunta_segura,
        tenant_id=tenant_id,
    )
    resultado = consultar_corpus_spdp(consulta)
    return {
        "pregunta": pregunta_segura,
        "respuesta": resultado.respuesta,
        "citas_normativas": resultado.citas_normativas,
        "confianza": resultado.confianza,
        "fuente_oficial_verificada": resultado.fuente_oficial_verificada,
    }
