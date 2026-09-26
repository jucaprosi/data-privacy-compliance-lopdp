from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
import enum

from app_core.database import get_db_session
from features.derechos_arco.domain.models import SolicitudARCO, TipoSolicitud, EstadoSolicitud

router = APIRouter(prefix="/arco", tags=["ARCO+"])

class SolicitudARCOSchema(BaseModel):
    id: UUID
    tenant_id: UUID
    tipo_solicitud: TipoSolicitud
    estado: EstadoSolicitud
    cedula_solicitante: str
    nombre_solicitante: str
    fecha_recepcion: datetime
    fecha_vencimiento: datetime
    evidencia_respuesta_hash: str | None = None
    
    model_config = ConfigDict(from_attributes=True)

@router.get("/solicitudes", response_model=List[SolicitudARCOSchema])
async def listar_solicitudes(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(SolicitudARCO))
    return result.scalars().all()

@router.post("/solicitudes", response_model=SolicitudARCOSchema)
async def crear_solicitud(solicitud: dict, session: AsyncSession = Depends(get_db_session)):
    # Mock implementation for POST
    from datetime import datetime, timezone, timedelta
    from uuid import uuid4
    nueva = SolicitudARCO(
        id=uuid4(),
        tenant_id=uuid4(), # This would come from context usually
        tipo_solicitud=TipoSolicitud.ACCESO,
        estado=EstadoSolicitud.RECIBIDA,
        cedula_solicitante=solicitud.get("cedula_solicitante", "9999999999"),
        nombre_solicitante=solicitud.get("nombre_solicitante", "Juan Perez"),
        fecha_recepcion=datetime.now(timezone.utc),
        fecha_vencimiento=datetime.now(timezone.utc) + timedelta(days=15)
    )
    session.add(nueva)
    await session.commit()
    await session.refresh(nueva)
    return nueva
