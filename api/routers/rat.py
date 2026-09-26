"""Enrutador REST para la Sala ADPA: RAT Maestro."""
from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.dependencies import obtener_tenant_id_actual, obtener_usuario_actual
from app_core.security import UsuarioContexto, AccionOperativa, validar_permiso_sod
from fastapi import APIRouter, Depends, HTTPException, status
from features.rat.rat_service import registrar_actividad_rat, listar_actividades_rat
from features.rat.domain.models import ActividadRAT, BaseLegitimacion, CategoriaTitular

router = APIRouter(prefix="/rat", tags=["Registro de Actividades de Tratamiento (RAT)"])

class CrearActividadRATRequest(BaseModel):
    codigo: str = Field(..., description="Código nemotécnico de la actividad (ej. RAT-RRHH-001)")
    nombre: str = Field(..., description="Nombre del tratamiento")
    area_responsable: str = Field(..., description="Área o gerencia custodia")
    finalidad: str = Field(..., description="Finalidad unívoca y legítima")
    base_legal: BaseLegitimacion = BaseLegitimacion.CONSENTIMIENTO
    categorias_titulares: List[CategoriaTitular] = Field(default_factory=list)
    datos_sensibles: bool = False
    volumen_titulares_estimado: int = 0
    transferencia_internacional: bool = False
    requiere_eipd: bool = False
    es_gran_escala: bool = False

@router.post("/actividades")
def crear_actividad(
    payload: CrearActividadRATRequest,
    usuario: UsuarioContexto = Depends(obtener_usuario_actual),
):
    """Registra o actualiza una actividad de tratamiento en el RAT maestro."""
    if not validar_permiso_sod(usuario, AccionOperativa.APROBAR_FINALIDAD_RAT):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Violación SoD: El DPO no puede modificar el RAT.")
    
    tenant_id = usuario.tenant_id
    actividad = ActividadRAT(
        tenant_id=tenant_id,
        codigo=payload.codigo,
        nombre=payload.nombre,
        area_responsable=payload.area_responsable,
        finalidad=payload.finalidad,
        base_legal=payload.base_legal,
        categorias_titulares=payload.categorias_titulares,
        datos_sensibles=payload.datos_sensibles,
        volumen_titulares_estimado=payload.volumen_titulares_estimado,
        transferencia_internacional=payload.transferencia_internacional,
        requiere_eipd=payload.requiere_eipd,
        es_gran_escala=payload.es_gran_escala,
    )
    guardada = registrar_actividad_rat(actividad)
    return {"status": "SUCCESS", "actividad": guardada}

@router.get("/actividades")
def listar_actividades(tenant_id: str = Depends(obtener_tenant_id_actual)):
    """Obtiene el inventario completo del RAT de la organización."""
    actividades = listar_actividades_rat(tenant_id)
    return {"tenant_id": tenant_id, "total": len(actividades), "actividades": actividades}
