from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_tenant_session
from features.derechos_arco import derechos_arco_service

router = APIRouter(prefix="/arco", tags=["ARCO+"])

class SolicitudARCOSchema(BaseModel):
    id: UUID
    tenant_id: UUID
    tipo_solicitud: derechos_arco_service.TipoSolicitud
    estado: derechos_arco_service.EstadoSolicitud
    cedula_solicitante: str
    nombre_solicitante: str
    fecha_recepcion: datetime
    fecha_vencimiento: datetime
    evidencia_respuesta_hash: str | None = None

    model_config = ConfigDict(from_attributes=True)

@router.get("/solicitudes", response_model=List[SolicitudARCOSchema])
async def listar_solicitudes(session: AsyncSession = Depends(get_tenant_session)):
    return await derechos_arco_service.listar_solicitudes_arco(session)

@router.post("/solicitudes", response_model=SolicitudARCOSchema)
async def crear_solicitud(solicitud: dict, session: AsyncSession = Depends(get_tenant_session)):
    return await derechos_arco_service.crear_solicitud_arco(session, solicitud)
