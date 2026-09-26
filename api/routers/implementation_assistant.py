# ¤¤frontend-architect
"""Orquesta compuertas ADPA; el contexto de cada organización vive en la petición."""
from fastapi import APIRouter, Header, HTTPException
from features.ai_copilot.ai_copilot_service import (
    ConsultaAsistente, RespuestaAsistente, responder_implementacion,
    sanitizar_consulta, estado_proveedor_asistente,
)
from features.regulacion_rag.regulacion_rag_service import (
    CORPUS_VERSION, buscar_fundamentos, obtener_guia_brecha,
)

router = APIRouter(prefix="/ai_copilot", tags=["Asistente de implementación"])


# ¤validar-tenant
def validar_tenant(tenant: str) -> None:
    if not tenant.strip() or len(tenant) > 120:
        raise HTTPException(status_code=400, detail="Contexto de organización inválido.")


# ¤estado-asistente
@router.get("/estado")
def estado_asistente(x_tenant_id: str = Header(...)):
    validar_tenant(x_tenant_id)
    return {**estado_proveedor_asistente(), "corpus_version": CORPUS_VERSION}


# ¤consultar-asistente
@router.post("/consulta", response_model=RespuestaAsistente)
async def consultar_asistente(payload: ConsultaAsistente, x_tenant_id: str = Header(...)):
    validar_tenant(x_tenant_id)
    segura = sanitizar_consulta(payload)
    guias = {
        b.pregunta_id: guia for b in segura.brechas
        if (guia := obtener_guia_brecha(b.pregunta_id, b.control, b.dimension_id)) is not None
    }
    fuentes = buscar_fundamentos(segura.pregunta)
    return await responder_implementacion(segura, guias, fuentes, CORPUS_VERSION)

