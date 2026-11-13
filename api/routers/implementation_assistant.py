# ¤¤frontend-architect
# ¤seguridad-tenant
"""Orquesta compuertas ADPA; el contexto de cada organización vive en la petición.

SEC-23: identidad y organización salen del token verificado (`obtener_tenant_id_actual`), que en modo
oidc exige token (401) y membresía activa en la organización de la cabecera (403). Se retiró el
antiguo `validar_tenant` (¤validar-tenant), que solo miraba la cabecera.
"""
from fastapi import APIRouter, Depends
from api.dependencies import obtener_tenant_id_actual
from features.ai_copilot.ai_copilot_service import (
    ConsultaAsistente, RespuestaAsistente, responder_implementacion,
    sanitizar_consulta, estado_proveedor_asistente,
)
from features.regulacion_rag.regulacion_rag_service import (
    CORPUS_VERSION, buscar_fundamentos, obtener_guia_brecha,
)

router = APIRouter(prefix="/ai_copilot", tags=["Asistente de implementación"])


# ¤estado-asistente
@router.get("/estado")
def estado_asistente(_tenant_id: str = Depends(obtener_tenant_id_actual)):
    return {**estado_proveedor_asistente(), "corpus_version": CORPUS_VERSION}


# ¤consultar-asistente
@router.post("/consulta", response_model=RespuestaAsistente)
async def consultar_asistente(
    payload: ConsultaAsistente, _tenant_id: str = Depends(obtener_tenant_id_actual),
):
    segura = sanitizar_consulta(payload)
    guias = {
        b.pregunta_id: guia for b in segura.brechas
        if (guia := obtener_guia_brecha(b.pregunta_id, b.control, b.dimension_id)) is not None
    }
    fuentes = buscar_fundamentos(segura.pregunta)
    return await responder_implementacion(segura, guias, fuentes, CORPUS_VERSION)
