from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, computed_field
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_tenant_session
from app_core.security import get_current_tenant
from features.derechos_arco import derechos_arco_service

router = APIRouter(prefix="/arco", tags=["ARCO+"])

class SolicitudARCOSchema(BaseModel):
    id: UUID
    tenant_id: str
    tipo_solicitud: derechos_arco_service.TipoSolicitud
    estado: derechos_arco_service.EstadoSolicitud
    cedula_solicitante: str
    nombre_solicitante: str
    fecha_recepcion: datetime
    fecha_vencimiento: datetime
    evidencia_respuesta_hash: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def plazo_dias(self) -> int:
        return derechos_arco_service.plazo_dias(self.tipo_solicitud)

    @computed_field
    @property
    def plazo_unidad(self) -> str:
        return derechos_arco_service.PLAZO_UNIDAD

    @computed_field
    @property
    def plazo_estimado(self) -> bool:
        return derechos_arco_service.PLAZO_ESTIMADO


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
    """Persiste la solicitud con el tenant de la identidad, nunca con el del cuerpo (por la compuerta)."""
    return await derechos_arco_service.crear_solicitud_arco(
        session, solicitud.model_dump(), tenant_id=tenant_id
    )
