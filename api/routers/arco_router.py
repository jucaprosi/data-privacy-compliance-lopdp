from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_tenant_session
from app_core.security import get_current_tenant
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


class CrearSolicitudARCOSchema(BaseModel):
    """Datos aportados por el operador; el tenant siempre procede de la sesión."""

    tipo_solicitud: derechos_arco_service.TipoSolicitud
    cedula_solicitante: str = Field(min_length=5, max_length=20)
    nombre_solicitante: str = Field(min_length=1, max_length=200)

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

@router.get("/solicitudes", response_model=List[SolicitudARCOSchema])
async def listar_solicitudes(session: AsyncSession = Depends(get_tenant_session)):
    return await derechos_arco_service.listar_solicitudes_arco(session)

@router.post("/solicitudes", response_model=SolicitudARCOSchema)
async def crear_solicitud(
    solicitud: CrearSolicitudARCOSchema,
    tenant_id: str = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_tenant_session),
):
    """Persiste la solicitud con el tenant de la identidad, nunca con el del cuerpo."""
    ahora = datetime.now(timezone.utc)
    nueva = derechos_arco_service.SolicitudARCO(
        id=uuid4(),
        tenant_id=UUID(tenant_id),
        tipo_solicitud=solicitud.tipo_solicitud,
        estado=derechos_arco_service.EstadoSolicitud.RECIBIDA,
        cedula_solicitante=solicitud.cedula_solicitante,
        nombre_solicitante=solicitud.nombre_solicitante,
        fecha_recepcion=ahora,
        fecha_vencimiento=ahora + timedelta(days=15),
    )
    session.add(nueva)
    await session.flush()
    await session.refresh(nueva)
    return nueva
