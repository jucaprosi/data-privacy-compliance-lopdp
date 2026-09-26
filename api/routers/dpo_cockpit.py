"""Enrutador REST para la Sala ADPA: Cockpit del DPD/DPO."""
from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.dependencies import obtener_tenant_id_actual
from features.dpo_cockpit.dpo_cockpit_service import (
    emitir_dictamen_dpo,
    consultar_bitacora_dpo,
    firmar_acuse_recibo_dictamen,
)
from features.dpo_cockpit.domain.models import DictamenDPO, TipoDictamenDPO

router = APIRouter(prefix="/dpo", tags=["Cockpit del DPD/DPO"])

class EmitirDictamenRequest(BaseModel):
    dpo_id: str = Field(..., description="ID del Delegado de Protección de Datos")
    tipo: TipoDictamenDPO = TipoDictamenDPO.OPINION_CONSULTIVA
    asunto: str = Field(..., description="Asunto o materia de la recomendación")
    referencia_normativa: str = Field(..., description="Artículos LOPDP o resoluciones aplicables")
    cuerpo: str = Field(..., description="Contenido técnico del dictamen")

@router.post("/dictamenes")
def emitir_dictamen(
    payload: EmitirDictamenRequest,
    tenant_id: str = Depends(obtener_tenant_id_actual),
):
    """Emite un dictamen consultivo no vinculante y lo asienta en la bitácora inviolable."""
    dictamen = DictamenDPO(
        tenant_id=tenant_id,
        dpo_id=payload.dpo_id,
        tipo=payload.tipo,
        asunto=payload.asunto,
        referencia_normativa=payload.referencia_normativa,
        cuerpo=payload.cuerpo,
    )
    guardado = emitir_dictamen_dpo(dictamen)
    return {"status": "SUCCESS", "dictamen": guardado}

@router.get("/bitacora")
def consultar_bitacora(tenant_id: str = Depends(obtener_tenant_id_actual)):
    """Recupera la bitácora histórica de diligencia del DPO."""
    historial = consultar_bitacora_dpo(tenant_id)
    return {"tenant_id": tenant_id, "total": len(historial), "dictamenes": historial}

@router.post("/dictamenes/{dictamen_id}/acuse")
def firmar_acuse(dictamen_id: str):
    """Registra la constancia formal de recepción del dictamen por la Alta Dirección."""
    dictamen = firmar_acuse_recibo_dictamen(dictamen_id)
    return {"status": "SUCCESS", "dictamen": dictamen}
