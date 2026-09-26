"""Enrutador REST para la Sala ADPA: Auditorías y Acciones Correctivas (CAPA)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import obtener_tenant_id_actual
from features.auditoria_capa.auditoria_capa_service import (
    registrar_hallazgo_auditoria,
    cerrar_accion_correctiva_independiente,
    consultar_hallazgos_tenant,
)
from features.auditoria_capa.domain.models import TicketCAPA, SeveridadHallazgo, EstadoCAPA

router = APIRouter(prefix="/capa", tags=["Auditorías y Acciones Correctivas (CAPA)"])

class CrearTicketCAPARequest(BaseModel):
    control_id: str = Field(..., description="ID del control auditado")
    severidad: SeveridadHallazgo = SeveridadHallazgo.NO_CONFORMIDAD_MENOR
    descripcion_hallazgo: str = Field(..., description="Descripción del hallazgo")
    causa_raiz: str = Field("", description="Análisis de causa raíz (ej. 5 Por qués)")
    accion_correctiva: str = Field(..., description="Plan de remediación acordado")
    responsable_implementacion_id: str = Field(..., description="Dueño operativo del control")

class CerrarTicketCAPARequest(BaseModel):
    auditor_id: str = Field(..., description="ID del auditor o verificador independiente")
    evidencia_id: str = Field(..., description="ID de la evidencia documental que soporta el cierre")

@router.post("/tickets")
def registrar_ticket(
    payload: CrearTicketCAPARequest,
    tenant_id: str = Depends(obtener_tenant_id_actual),
):
    """Registra una no conformidad u oportunidad de mejora."""
    ticket = TicketCAPA(
        tenant_id=tenant_id,
        control_id=payload.control_id,
        severidad=payload.severidad,
        descripcion_hallazgo=payload.descripcion_hallazgo,
        causa_raiz=payload.causa_raiz,
        accion_correctiva=payload.accion_correctiva,
        responsable_implementacion_id=payload.responsable_implementacion_id,
    )
    guardado = registrar_hallazgo_auditoria(ticket)
    return {"status": "SUCCESS", "ticket": guardado}

@router.get("/tickets")
def listar_tickets(tenant_id: str = Depends(obtener_tenant_id_actual)):
    """Obtiene todos los tickets CAPA del tenant."""
    tickets = consultar_hallazgos_tenant(tenant_id)
    return {"tenant_id": tenant_id, "total": len(tickets), "tickets": tickets}

from api.dependencies import obtener_tenant_id_actual, obtener_usuario_actual
from app_core.security import UsuarioContexto, AccionOperativa, validar_permiso_sod

@router.post("/tickets/{ticket_id}/cerrar")
def cerrar_ticket(
    ticket_id: str,
    payload: CerrarTicketCAPARequest,
    usuario: UsuarioContexto = Depends(obtener_usuario_actual)
):
    """Cierra un hallazgo tras verificar la eficacia con un rol independiente (SoD estricto)."""
    if not validar_permiso_sod(usuario, AccionOperativa.EJECUTAR_REMEDIACION_CAPA):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Violación SoD: El DPO no puede cerrar tickets CAPA directamente.")
    
    try:
        ticket = cerrar_accion_correctiva_independiente(
            ticket_id=ticket_id,
            auditor_id=payload.auditor_id,
            evidencia_id=payload.evidencia_id,
        )
        return {"status": "SUCCESS", "ticket": ticket}
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except KeyError as ke:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ke))
